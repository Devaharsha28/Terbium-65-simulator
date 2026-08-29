using System.IO;
using System.Linq;
using Seb.Helpers;
using Seb.Vis;
using Seb.Vis.UI;
using UnityEngine;
using static Seb.Helpers.ColHelper;

namespace DLS.Graphics
{
	/// <summary>
	/// Central manager for the active color palette.
	/// Rebuilds DrawSettings.ActiveTheme and DrawSettings.ActiveUITheme whenever
	/// the palette changes, so all UI picks up the new colors immediately.
	/// </summary>
	public static class ThemeManager
	{
		// ---- Built-in presets ----

		public const string PresetName_TerbiumDark = "Terbium Dark";
		public const string PresetName_Custom = "Custom";

		public static readonly string[] PresetNames = { PresetName_TerbiumDark, PresetName_Custom };

		public static readonly ThemePalette TerbiumDarkPalette = new ThemePalette(); // defaults are the Terbium Dark values

		// ---- Active state ----

		public static ThemePalette ActivePalette { get; private set; } = TerbiumDarkPalette.Clone();
		public static string ActivePresetName { get; private set; } = PresetName_TerbiumDark;

		// ---- Persistence ----

		static string SavePath => Path.Combine(Application.persistentDataPath, "theme.json");

		// ---- Initialization ----

		public static void Initialize()
		{
			TryLoad();
			Apply(ActivePalette);
		}

		// ---- Public API ----

		/// <summary>Apply a palette immediately (rebuilds DrawSettings themes).</summary>
		public static void Apply(ThemePalette palette)
		{
			ActivePalette = palette;
			RebuildDrawSettings(palette);
		}

		/// <summary>Apply a single semantic color by field name, then rebuild.</summary>
		public static void SetColor(string fieldName, Color color)
		{
			var field = typeof(ThemePalette).GetField(fieldName);
			if (field == null) return;
			field.SetValue(ActivePalette, ThemePalette.ToHex(color));

			// If it no longer matches Terbium Dark, switch to Custom preset
			ActivePresetName = IsDefaultPalette(ActivePalette) ? PresetName_TerbiumDark : PresetName_Custom;
			RebuildDrawSettings(ActivePalette);
		}

		/// <summary>Set a single semantic color from a hex string.</summary>
		public static bool SetColorHex(string fieldName, string hex)
		{
			// Validate it's a real color first
			if (!ColorUtility.TryParseHtmlString(hex.StartsWith("#") ? hex : "#" + hex, out Color _))
				return false;
			var field = typeof(ThemePalette).GetField(fieldName);
			if (field == null) return false;
			field.SetValue(ActivePalette, hex.StartsWith("#") ? hex : "#" + hex);
			ActivePresetName = IsDefaultPalette(ActivePalette) ? PresetName_TerbiumDark : PresetName_Custom;
			RebuildDrawSettings(ActivePalette);
			return true;
		}

		/// <summary>Get the current hex string for a field name.</summary>
		public static string GetHex(string fieldName)
		{
			var field = typeof(ThemePalette).GetField(fieldName);
			return field?.GetValue(ActivePalette) as string ?? "#FF00FF";
		}

		/// <summary>Resets the palette to the built-in Terbium Dark defaults.</summary>
		public static void ResetToDefault()
		{
			ActivePalette = TerbiumDarkPalette.Clone();
			ActivePresetName = PresetName_TerbiumDark;
			RebuildDrawSettings(ActivePalette);
		}

		/// <summary>Save current palette to disk.</summary>
		public static void Save()
		{
			var data = new SaveData { presetName = ActivePresetName, palette = ActivePalette };
			File.WriteAllText(SavePath, JsonUtility.ToJson(data, true));
		}

		// ---- Private helpers ----

		static void TryLoad()
		{
			if (!File.Exists(SavePath)) return;
			try
			{
				var data = JsonUtility.FromJson<SaveData>(File.ReadAllText(SavePath));
				if (data?.palette != null)
				{
					ActivePalette = data.palette;
					ActivePresetName = data.presetName ?? PresetName_Custom;
				}
			}
			catch
			{
				// Silently fall back to default if JSON is corrupt
				ActivePalette = TerbiumDarkPalette.Clone();
				ActivePresetName = PresetName_TerbiumDark;
			}
		}

		static bool IsDefaultPalette(ThemePalette p)
		{
			ThemePalette d = TerbiumDarkPalette;
			// Quick structural compare across all string fields
			foreach (var f in typeof(ThemePalette).GetFields())
			{
				if (f.GetValue(p) as string != f.GetValue(d) as string) return false;
			}
			return true;
		}

		/// <summary>
		/// Rebuilds DrawSettings.ActiveTheme and DrawSettings.ActiveUITheme in-place
		/// using the semantic colors from the supplied palette.
		/// </summary>
		static void RebuildDrawSettings(ThemePalette p)
		{
			Color background    = ThemePalette.Parse(p.Background);
			Color workspace     = ThemePalette.Parse(p.Workspace);
			Color panel         = ThemePalette.Parse(p.Panel);
			Color panelElevated = ThemePalette.Parse(p.PanelElevated);
			Color border        = ThemePalette.Parse(p.Border);
			Color accent        = ThemePalette.Parse(p.Accent);
			Color accentHover   = ThemePalette.Parse(p.AccentHover);
			Color textPrimary   = ThemePalette.Parse(p.TextPrimary);
			Color textSecondary = ThemePalette.Parse(p.TextSecondary);
			Color textDisabled  = ThemePalette.Parse(p.TextDisabled);
			Color error         = ThemePalette.Parse(p.Error);
			Color warning       = ThemePalette.Parse(p.Warning);
			Color tritNeg       = ThemePalette.Parse(p.TritNegative);
			Color tritZero      = ThemePalette.Parse(p.TritZero);
			Color tritPos       = ThemePalette.Parse(p.TritPositive);

			// ---- Rebuild ThemeDLS (world/simulation colors) ----
			DrawSettings.ThemeDLS t = DrawSettings.ActiveTheme;

			Color[] stateLow   = Enumerable.Repeat(tritNeg, 8).ToArray();
			Color[] stateHigh  = Enumerable.Repeat(tritPos, 8).ToArray();
			Color[] stateHover = stateLow.Select(c => Brighten(c, 0.075f)).ToArray();

			t.BackgroundCol                  = background;
			t.GridCol                        = workspace;
			t.StateLowCol                    = stateLow;
			t.StateHighCol                   = stateHigh;
			t.StateHoverCol                  = stateHover;
			t.StateDisconnectedCol           = tritZero;
			t.SelectionBoxCol                = new Color(1, 1, 1, 0.1f);
			t.SelectionBoxMovingCol          = new Color(1, 1, 1, 0.125f);
			t.SelectionBoxInvalidCol         = WithAlpha(error, 0.5f);
			t.SelectionBoxOtherIsInvaldCol   = WithAlpha(warning, 0.5f);
			t.DevPinHandle                   = border;
			t.DevPinHandleHighlighted        = accent;
			t.PinCol                         = panel;
			t.PinLabelCol                    = textSecondary;
			t.PinHighlightCol                = tritPos;
			t.PinInvalidCol                  = error;
			t.SevenSegCols                   = new[]
			{
				workspace, tritPos, accent,  // Col A: OFF, ON, HIGHLIGHT
				workspace, tritPos, accent   // Col B: OFF, ON, HIGHLIGHT
			};

			// ---- Rebuild UIThemeDLS (menu / UI colors) ----
			DrawSettings.UIThemeDLS ui = DrawSettings.ActiveUITheme;

			FontType fontRegular = DrawSettings.FontRegular;
			FontType fontBold    = DrawSettings.FontBold;
			float fontSize       = UIThemeLibrary.FontSizeMedium;

			ui.MenuPanelCol              = panel;
			ui.MenuBackgroundOverlayCol  = new Color(0, 0, 0, 0.85f);
			ui.InfoBarCol                = WithAlpha(background, 0.9f);
			ui.StarredBarCol             = panelElevated;
			ui.ButtonTheme               = MakeBtn(fontRegular, fontSize, panelElevated, border,       accent,     textPrimary, textPrimary, textPrimary, panel, textDisabled);
			ui.ProjectSelectionButton    = MakeBtn(fontRegular, fontSize, Color.clear,   panelElevated, accent,     textPrimary, textPrimary, textPrimary, panel, textDisabled);
			ui.ProjectSelectionButtonSelected = MakeBtn(fontRegular, fontSize, accent,  accentHover,   tritPos,    background,  background,  background,  panel, textDisabled);
			ui.ChipButton                = MakeBtn(fontRegular, fontSize, panel,         panelElevated, accent,     textPrimary, textPrimary, textPrimary, panel, textDisabled);
			ui.MainMenuButtonTheme       = MakeBtn(fontRegular, fontSize, panelElevated, accent,        tritPos,    textPrimary, textPrimary, textPrimary, panel, textDisabled);
			ui.MenuButtonTheme           = MakeBtn(fontRegular, fontSize, panel,         accent,        tritPos,    textPrimary, textPrimary, textPrimary, panel, textDisabled);
			ui.MenuPopupButtonTheme      = MakeBtn(fontRegular, fontSize, background,    panelElevated, border,     textPrimary, textPrimary, textPrimary, panel, textDisabled);

			Color colLibCollHighlight    = accentHover;
			Color colLibChipHighlight    = tritPos;
			ui.ChipLibraryCollectionToggleOff = MakeBtn(fontRegular, fontSize, panelElevated, border, colLibCollHighlight, textPrimary, textPrimary, textPrimary, panel, textDisabled);
			ui.ChipLibraryCollectionToggleOn  = MakeBtnAuto(fontRegular, fontSize, colLibCollHighlight, background, panel, textDisabled);
			ui.ChipLibraryChipToggleOff       = MakeBtn(fontRegular, fontSize, panel, border, colLibChipHighlight, textPrimary, textPrimary, textPrimary, panel, textDisabled);
			ui.ChipLibraryChipToggleOn        = MakeBtnAuto(fontRegular, fontSize, colLibChipHighlight, background, panel, textDisabled);

			ui.ChipNameInputField = new InputFieldTheme
			{
				font           = fontBold,
				fontSize       = UIThemeLibrary.FontSizeVeryLarge,
				bgCol          = workspace,
				defaultTextCol = textSecondary,
				textCol        = textPrimary,
				focusBorderCol = accent
			};

			ui.OptionsWheel = new WheelSelectorTheme
			{
				backgroundCol = panel,
				buttonTheme   = MakeBtn(fontBold, fontSize, panelElevated, accent, tritPos, textPrimary, textPrimary, textPrimary, panel, textDisabled),
				textCol       = textPrimary,
				inactiveTextCol = textSecondary
			};

			ui.ScrollTheme = new ScrollViewTheme
			{
				backgroundCol       = background,
				padding             = 1,
				scrollBarColBackground = panel,
				scrollBarColInactive   = panelElevated,
				scrollBarColNormal     = border,
				scrollBarColHover      = accent,
				scrollBarColPressed    = tritPos,
				scrollBarWidth         = 1
			};

			ui.CheckBoxTheme = new CheckboxTheme
			{
				boxCol  = textPrimary,
				tickCol = workspace
			};
		}

		static ButtonTheme MakeBtn(FontType font, float fontSize,
			Color normal, Color hover, Color press,
			Color textNormal, Color textHover, Color textPress,
			Color inactive, Color textInactive)
		{
			return new ButtonTheme
			{
				font         = font,
				fontSize     = fontSize,
				paddingScale = UIThemeLibrary.PaddingScaleButton,
				buttonCols   = new ButtonTheme.StateCols(normal, hover, press, inactive),
				textCols     = new ButtonTheme.StateCols(textNormal, textHover, textPress, textInactive)
			};
		}

		static ButtonTheme MakeBtnAuto(FontType font, float fontSize, Color normal, Color textCol, Color inactive, Color textInactive)
		{
			Color hover  = Brighten(normal, 0.2f, -0.1f);
			Color press  = Darken(normal, 0.05f, 0.05f);
			return MakeBtn(font, fontSize, normal, hover, press, textCol, textCol, textCol, inactive, textInactive);
		}

		[System.Serializable]
		class SaveData
		{
			public string       presetName;
			public ThemePalette palette;
		}
	}
}
