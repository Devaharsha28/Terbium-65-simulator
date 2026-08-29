using DLS.Game;
using Seb.Helpers;
using Seb.Types;
using Seb.Vis;
using Seb.Vis.UI;
using UnityEngine;

namespace DLS.Graphics
{
	/// <summary>
	/// Draws the Theme Editor sub-screen that lives inside the Settings area of MainMenu.
	/// Call DrawThemeEditor() from within the MainMenu settings screen switch-case.
	/// </summary>
	public static class ThemeEditorMenu
	{
		// ---- Layout ----
		const float MenuWidth     = 70f;
		const float SwatchSize    = 3f;
		const float RowHeight     = 3.5f;
		const float RowSpacing    = 0.6f;
		const float LabelWidth    = 28f;
		const float HexFieldWidth = 20f;

		// ---- UI Handles ----
		// We create one handle per color field (named by field name).
		static UIHandle GetHexHandle(string fieldName) => new("ThemeEditor_Hex_" + fieldName);

		// Preset wheel
		static readonly UIHandle ID_PresetWheel = new("ThemeEditor_PresetWheel");

		// Track initialization per open session
		static bool initialized;

		// ---- Color groups ----

		static readonly (string label, string field)[] InterfaceColors =
		{
			("Background",     "Background"),
			("Workspace",      "Workspace"),
			("Panel",          "Panel"),
			("Elevated Panel", "PanelElevated"),
			("Border",         "Border"),
			("Accent",         "Accent"),
			("Accent Hover",   "AccentHover"),
			("Primary Text",   "TextPrimary"),
			("Secondary Text", "TextSecondary"),
			("Disabled Text",  "TextDisabled"),
		};

		static readonly (string label, string field)[] SemanticColors =
		{
			("Success", "Success"),
			("Warning", "Warning"),
			("Error",   "Error"),
		};

		static readonly (string label, string field)[] TernaryColors =
		{
			("\u22121 (Low)",      "TritNegative"),
			("0 (Disconnected)",   "TritZero"),
			("+1 (High)",          "TritPositive"),
		};

		// ---- Public API ----

		public static void OnMenuOpened()
		{
			initialized = false;
		}

		/// <summary>
		/// Main draw call. Returns true when the user clicks "Back".
		/// topLeft should be the top-left of the available content area.
		/// </summary>
		public static bool Draw(Vector2 centre)
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;

			float scrollAreaWidth  = MenuWidth;
			float scrollAreaHeight = 22f; // Reduced so it doesn't push the buttons off the screen

			// Initialize hex fields from current palette on first draw
			if (!initialized)
			{
				initialized = true;
				InitHexFields();
			}

			using (UI.BeginBoundsScope(true))
			{
				Draw.ID panelID = UI.ReservePanel();

				// Keep it below the TERBIUM 65 logo
				Vector2 topLeft = centre + new Vector2(-MenuWidth / 2f, 12f);
				Vector2 pos     = topLeft;

				// ---- Preset controls ----
				Color headerCol = ColHelper.MakeCol("#4C8DFF");
				DrawSectionHeader(ref pos, "THEME PRESET", headerCol, theme);

				// Preset wheel
				string[] presetNames = ThemeManager.PresetNames;
				int currPresetIdx    = ThemeManager.ActivePresetName == ThemeManager.PresetName_TerbiumDark ? 0 : 1;
				Vector2 wheelSize    = new(22f, DrawSettings.SelectorWheelHeight);
				UI.DrawText("Preset", theme.FontRegular, theme.FontSizeRegular,
					pos, Anchor.CentreLeft, Color.white);
				int chosenPreset = UI.WheelSelector(ID_PresetWheel, presetNames,
					pos + Vector2.right * (MenuWidth - wheelSize.x), wheelSize, theme.OptionsWheel, Anchor.CentreLeft);
				pos.y -= RowHeight + RowSpacing;

				if (chosenPreset == 0 && ThemeManager.ActivePresetName != ThemeManager.PresetName_TerbiumDark)
				{
					ThemeManager.ResetToDefault();
					InitHexFields();
				}

				// Reset button
				Vector2 resetBtnSize = new(28f, DrawSettings.ButtonHeight);
				if (UI.Button("RESET TO TERBIUM DEFAULT", theme.MenuButtonTheme, pos, resetBtnSize, true, false, false, Anchor.CentreLeft))
				{
					ThemeManager.ResetToDefault();
					InitHexFields();
					UI.GetWheelSelectorState(ID_PresetWheel).index = 0;
				}
				pos.y -= resetBtnSize.y + RowSpacing * 2;

				// ---- Scroll view for colors ----
				Vector2 scrollPos  = new(centre.x, pos.y - scrollAreaHeight / 2f);
				Vector2 scrollSize = new(scrollAreaWidth, scrollAreaHeight);

				UI.DrawScrollView(new UIHandle("ThemeEditor_Scroll"), scrollPos, scrollSize,
					Anchor.Centre, theme.ScrollTheme, DrawScrollContent);

				pos.y -= scrollAreaHeight + RowSpacing;

				// ---- Save button ----
				Vector2 saveBtnSize = new(18f, DrawSettings.ButtonHeight);
				bool saveClicked = UI.Button("SAVE THEME", theme.MainMenuButtonTheme,
					pos, saveBtnSize, true, false, false, Anchor.CentreLeft);
				if (saveClicked) ThemeManager.Save();

				// Back button
				Vector2 backBtnPos  = pos + Vector2.right * (saveBtnSize.x + 2f);
				bool backClicked = UI.Button("BACK", theme.MainMenuButtonTheme,
					backBtnPos, new Vector2(12f, DrawSettings.ButtonHeight), true, false, false, Anchor.CentreLeft);

				// Panel background
				Bounds2D bounds = UI.GetCurrentBoundsScope();
				UI.ModifyPanel(panelID, bounds.Centre, bounds.Size + Vector2.one * 3f, theme.MenuPanelCol);

				return backClicked || KeyboardShortcuts.CancelShortcutTriggered;
			}
		}

		// ---- Private ----

		static void DrawScrollContent(Vector2 topLeft, float width, bool isLayoutPass)
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;
			Color headerCol               = ColHelper.MakeCol("#4C8DFF");
			Vector2 pos                   = topLeft + Vector2.down * 1f;

			DrawColorGroup(ref pos, width, "INTERFACE", InterfaceColors, headerCol, theme, isLayoutPass);
			DrawColorGroup(ref pos, width, "SEMANTIC UI", SemanticColors, headerCol, theme, isLayoutPass);
			DrawColorGroup(ref pos, width, "TERNARY LOGIC", TernaryColors, headerCol, theme, isLayoutPass);
		}

		static void DrawColorGroup(ref Vector2 pos, float width,
			string groupTitle, (string label, string field)[] colors,
			Color headerCol, DrawSettings.UIThemeDLS theme, bool isLayoutPass)
		{
			DrawSectionHeader(ref pos, groupTitle, headerCol, theme);

			foreach (var (label, field) in colors)
			{
				DrawColorRow(ref pos, width, label, field, theme, isLayoutPass);
			}
			pos.y -= RowSpacing * 2;
		}

		static void DrawColorRow(ref Vector2 pos, float width,
			string label, string fieldName,
			DrawSettings.UIThemeDLS theme, bool isLayoutPass)
		{
			// Label
			UI.DrawText(label, theme.FontRegular, theme.FontSizeRegular,
				pos, Anchor.CentreLeft, Color.white);

			// Color swatch (drawn as a filled panel)
			Color currentColor = ThemePalette.Parse(ThemeManager.GetHex(fieldName));
			Vector2 swatchPos  = pos + new Vector2(LabelWidth, 0);
			Vector2 swatchSz   = new(SwatchSize, SwatchSize);
			UI.DrawPanel(swatchPos, swatchSz, currentColor, Anchor.CentreLeft);

			// HEX input field
			UIHandle hexHandle = GetHexHandle(fieldName);
			Vector2 hexPos     = swatchPos + new Vector2(swatchSz.x + 1f, 0);
			Vector2 hexSize    = new(HexFieldWidth, RowHeight * 0.9f);

			InputFieldTheme hexInputTheme = new InputFieldTheme
			{
				font           = theme.FontRegular,
				fontSize       = theme.FontSizeRegular,
				bgCol          = ColHelper.MakeCol("#1C1E23"),
				defaultTextCol = ColHelper.MakeCol("#5F646B"),
				textCol        = Color.white,
				focusBorderCol = ColHelper.MakeCol("#4C8DFF")
			};

			InputFieldState hexState = UI.InputField(hexHandle, hexInputTheme,
				hexPos, hexSize, "#", Anchor.CentreLeft, 0.5f,
				s => ValidateHex(s), false);

			// Apply on submit or when field loses focus and has a valid 6-char hex
			if (IsValidFullHex(hexState.text))
			{
				string incoming = NormalizeHex(hexState.text);
				if (incoming != ThemeManager.GetHex(fieldName))
				{
					ThemeManager.SetColorHex(fieldName, incoming);
				}
			}

			pos.y -= RowHeight + RowSpacing;
		}

		static void DrawSectionHeader(ref Vector2 pos, string text, Color col, DrawSettings.UIThemeDLS theme)
		{
			pos.y -= RowSpacing;
			UI.DrawText(text, theme.FontBold, theme.FontSizeRegular, pos, Anchor.CentreLeft, col);
			pos.y -= RowHeight * 0.85f + RowSpacing;
		}

		static void InitHexFields()
		{
			foreach (var (_, field) in InterfaceColors)
				SetHexField(field);
			foreach (var (_, field) in SemanticColors)
				SetHexField(field);
			foreach (var (_, field) in TernaryColors)
				SetHexField(field);
		}

		static void SetHexField(string fieldName)
		{
			string hex = ThemeManager.GetHex(fieldName);
			UI.GetInputFieldState(GetHexHandle(fieldName)).SetText(hex, false);
		}

		static bool ValidateHex(string s)
		{
			if (string.IsNullOrEmpty(s)) return true;
			string clean = s.TrimStart('#');
			if (clean.Length > 6) return false;
			foreach (char c in clean)
			{
				bool valid = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
				if (!valid) return false;
			}
			return true;
		}

		static bool IsValidFullHex(string s)
		{
			string clean = s.TrimStart('#');
			return clean.Length == 6 && ValidateHex(s);
		}

		static string NormalizeHex(string s)
		{
			string clean = s.TrimStart('#');
			return "#" + clean.ToUpper();
		}
	}
}
