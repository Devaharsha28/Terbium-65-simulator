using System.Linq;
using Seb.Vis;
using Seb.Vis.UI;
using UnityEngine;
using static Seb.Helpers.ColHelper;

namespace DLS.Graphics
{
	public static class DrawSettings
	{
		// ---- World draw settings ----
		public const float GridSize = 0.125f;
		public const float PinHeight1Bit = 0.185f;
		public const float PinHeight4Bit = 0.3f;
		public const float PinHeight8Bit = 0.43f;
		public const float PinRadius = PinHeight1Bit / 2;

		public const FontType FontBold = FontType.JetbrainsMonoBold;
		public const FontType FontRegular = FontType.JetbrainsMonoRegular;

		public const float FontSizeChipName = 0.25f;
		public const float FontSizePinLabel = 0.2f;

		public const float SubChipPinInset = 0.015f;
		public const float SelectionBoundsPadding = 0.08f;
		public const float ChipOutlineWidth = 0.05f;
		public const float WireThickness = 0.025f;
		public const float WireHighlightedThickness = WireThickness + 0.012f;
		public const float GridThickness = 0.0035f;
		public const float DevPinStateDisplayRadius = 0.2f;
		public const float DevPinStateDisplayOutline = 0.0175f;
		public const float DevPinHandleWidth = DevPinStateDisplayRadius * 0.64f;
		public const float MultiBitPinStateDisplaySquareSize = 0.21f;

		// ---- UI draw settings ----
		public const float PanelUIPadding = 1.15f * 2;
		public const float SpacingUnitUI = 0.5f;
		public const float ChipNameLineSpacing = 0.75f;
		public const float VerticalButtonSpacing = 1f;
		public const float HorizontalButtonSpacing = 0.5f;
		public const float SelectorWheelHeight = 2.8f;
		public const float ButtonHeight = 2.5f;

		public const float DefaultButtonSpacing = SpacingUnitUI * 1;
		public const float InfoBarHeight = 3.5f;
		public static readonly Vector2 LabelBackgroundPadding = new(0.15f, 0.1f);

		// ---- Themes ----
		// NOTE: Not readonly — ThemeManager mutates these at runtime when colors change.
		public static ThemeDLS ActiveTheme = CreateTheme();
		public static UIThemeDLS ActiveUITheme = CreateUITheme();

		// ---- Helper functions ----
		public static Color GetStateColour(bool isHigh, uint index, bool hover = false)
		{
			index = (uint)Mathf.Min(index, ActiveTheme.StateHighCol.Length - 1); // clamp just to be safe...
			if (!isHigh && hover) return ActiveTheme.StateHoverCol[index];
			return isHigh ? ActiveTheme.StateHighCol[index] : ActiveTheme.StateLowCol[index];
		}

		static ThemeDLS CreateTheme()
		{
			Color[] stateLow = Enumerable.Repeat(MakeCol("#FF6B6B"), 8).ToArray();
			Color[] stateHigh = Enumerable.Repeat(MakeCol("#5B9FE3"), 8).ToArray();
			Color[] stateHover = stateLow.Select(c => Brighten(c, 0.075f)).ToArray();

			return new ThemeDLS
			{
				SelectionBoxCol = new Color(1, 1, 1, 0.1f),
				SelectionBoxMovingCol = new Color(1, 1, 1, 0.125f),
				SelectionBoxInvalidCol = WithAlpha(MakeCol("#D65A5A"), 0.5f),
				SelectionBoxOtherIsInvaldCol = WithAlpha(MakeCol("#EBC870"), 0.5f),
				StateLowCol = stateLow,
				StateHighCol = stateHigh,
				StateHoverCol = stateHover,
				StateDisconnectedCol = MakeCol("#858B93"),
				DevPinHandle = MakeCol("#4C5059"),
				DevPinHandleHighlighted = MakeCol("#4C8DFF"),
				PinCol = MakeCol("#26292E"),
				PinLabelCol = MakeCol("#A4ADB5"),
				PinHighlightCol = MakeCol("#5B9FE3"),
				PinInvalidCol = MakeCol("#D65A5A"),
				SevenSegCols = new Color[]
				{
					MakeCol("#1C1E23"), MakeCol("#5B9FE3"), MakeCol("#4C8DFF"), // Col A: OFF, ON, HIGHLIGHT
					MakeCol("#1C1E23"), MakeCol("#5B9FE3"), MakeCol("#4C8DFF") // Col B: OFF, ON, HIGHLIGHT
				},
				BackgroundCol = MakeCol("#1C1E23"),
				GridCol = MakeCol("#26292E"),
			};
		}

		static UIThemeDLS CreateUITheme()
		{
			FontType fontRegular = FontRegular;
			FontType fontBold = FontBold;
			float fontSizeRegular = UIThemeLibrary.FontSizeMedium;

			Color primaryText = MakeCol("#F5F7FA");
			Color secondaryText = MakeCol("#A4ADB5");
			Color disabledText = MakeCol("#707780");

			Color inactiveButtonCol = MakeCol("#26292E");
			Color inactiveTextol = disabledText;
			Color chipLibaryButtonOff = MakeCol("#31343A");
			Color chipLibaryButtonOn = MakeCol("#4C8DFF");
			Color menuPanelCol = MakeCol("#26292E");

			Color chipLibraryCollectionHighlightCol = MakeCol("#6A9EFF");
			Color chipLibraryChipHighlightCol = MakeCol("#5B9FE3");

			Color scrollBarCol = MakeCol("#4C5059");

			return new UIThemeDLS
			{
				// --- Text settings ---
				FontRegular = fontRegular,
				FontBold = fontBold,
				FontSizeRegular = fontSizeRegular,

				// --- Menu colours ---
				MenuPanelCol = menuPanelCol,
				MenuBackgroundOverlayCol = new Color(0, 0, 0, 0.85f),
				// --- Buttons ---
				ButtonTheme = MakeButtonTheme(fontRegular, MakeCol("#31343A"), MakeCol("#4C5059"), MakeCol("#4C8DFF"), primaryText, primaryText, primaryText),
				ProjectSelectionButton = MakeButtonTheme(fontRegular, Color.clear, MakeCol("#31343A"), MakeCol("#4C8DFF"), primaryText, primaryText, primaryText),
				ProjectSelectionButtonSelected = MakeButtonTheme(fontRegular, MakeCol("#4C8DFF"), MakeCol("#6A9EFF"), MakeCol("#5B9FE3"), MakeCol("#121417"), MakeCol("#121417"), MakeCol("#121417")),
				ChipButton = MakeButtonTheme(fontRegular, MakeCol("#26292E"), MakeCol("#31343A"), MakeCol("#4C8DFF"), primaryText, primaryText, primaryText),
				MainMenuButtonTheme = MakeButtonTheme(fontRegular, MakeCol("#31343A"), MakeCol("#4C8DFF"), MakeCol("#5B9FE3"), primaryText, primaryText, primaryText),
				MenuButtonTheme = MakeButtonTheme(fontRegular, MakeCol("#26292E"), MakeCol("#4C8DFF"), MakeCol("#5B9FE3"), primaryText, primaryText, primaryText),
				MenuPopupButtonTheme = MakeButtonThemeFull(fontRegular, MakeCol("#121417"), MakeCol("#31343A"), MakeCol("#4C5059"), inactiveButtonCol, primaryText, primaryText, primaryText, inactiveTextol),

				ChipLibraryCollectionToggleOff = MakeButtonTheme(fontRegular, MakeCol("#31343A"), MakeCol("#4C5059"), chipLibraryCollectionHighlightCol, primaryText, primaryText, primaryText),
				ChipLibraryCollectionToggleOn = MakeButtonThemeAuto(fontRegular, chipLibraryCollectionHighlightCol, MakeCol("#121417")),
				ChipLibraryChipToggleOff = MakeButtonTheme(fontRegular, MakeCol("#26292E"), MakeCol("#4C5059"), chipLibraryChipHighlightCol, primaryText, primaryText, primaryText),
				ChipLibraryChipToggleOn = MakeButtonThemeAuto(fontRegular, chipLibraryChipHighlightCol, MakeCol("#121417")),

				// --- Other stuff ---
				ChipNameInputField = new InputFieldTheme
				{
					font = fontBold,
					fontSize = UIThemeLibrary.FontSizeVeryLarge,
					bgCol = MakeCol("#1C1E23"),
					defaultTextCol = secondaryText,
					textCol = primaryText,
					focusBorderCol = MakeCol("#4C8DFF")
				},
				OptionsWheel = new WheelSelectorTheme
				{
					backgroundCol = MakeCol("#26292E"),
					buttonTheme = MakeButtonTheme(fontBold, MakeCol("#31343A"), MakeCol("#4C8DFF"), MakeCol("#5B9FE3"), primaryText, primaryText, primaryText),
					textCol = primaryText,
					inactiveTextCol = secondaryText
				},
				ScrollTheme = new ScrollViewTheme
				{
					backgroundCol = MakeCol("#121417"),
					padding = 1,
					scrollBarColBackground = MakeCol("#26292E"),
					scrollBarColInactive = MakeCol("#31343A"),
					scrollBarColNormal = MakeCol("#4C5059"),
					scrollBarColHover = MakeCol("#4C8DFF"),
					scrollBarColPressed = MakeCol("#5B9FE3"),
					scrollBarWidth = 1
				},
				CheckBoxTheme = new CheckboxTheme
				{
					boxCol = primaryText,
					tickCol = MakeCol("#1C1E23")
				},
				InfoBarCol = WithAlpha(MakeCol("#121417"), 0.9f),
				StarredBarCol = MakeCol("#31343A")
			};

			ButtonTheme MakeButtonThemeAuto(FontType font, Color colNormal, Color textCol)
			{
				Color colHover = Brighten(colNormal, 0.2f, -0.1f);
				Color colPress = Darken(colNormal, 0.05f, 0.05f);
				return MakeButtonThemeFull(font, colNormal, colHover, colPress, inactiveButtonCol, textCol, textCol, textCol, inactiveTextol);
			}

			ButtonTheme MakeButtonTheme(FontType font, Color colNormal, Color colHover, Color colPress, Color textNormal, Color textHover, Color textPress)
			{
				return MakeButtonThemeFull(font, colNormal, colHover, colPress, inactiveButtonCol, textNormal, textHover, textPress, inactiveTextol);
			}

			ButtonTheme MakeButtonThemeFull(FontType font, Color colNormal, Color colHover, Color colPress, Color colInactive, Color textNormal, Color textHover, Color textPress, Color textInactive)
			{
				return new ButtonTheme
				{
					font = font,
					fontSize = fontSizeRegular,
					paddingScale = UIThemeLibrary.PaddingScaleButton,
					buttonCols = new ButtonTheme.StateCols(colNormal, colHover, colPress, colInactive),
					textCols = new ButtonTheme.StateCols(textNormal, textHover, textPress, textInactive)
				};
			}
		}


		public class ThemeDLS
		{
			public Color BackgroundCol;
			public Color DevPinHandle;
			public Color DevPinHandleHighlighted;
			public Color GridCol;
			public Color PinCol;
			public Color PinHighlightCol;
			public Color PinInvalidCol;
			public Color PinLabelCol;
			public Color SelectionBoxCol;
			public Color SelectionBoxInvalidCol;
			public Color SelectionBoxMovingCol;
			public Color SelectionBoxOtherIsInvaldCol;
			public Color[] SevenSegCols; // Off, On, Highlight
			public Color StateDisconnectedCol;
			public Color[] StateHighCol;
			public Color[] StateHoverCol;
			public Color[] StateLowCol;
		}

		public class UIThemeDLS
		{
			public ButtonTheme ButtonTheme;
			public CheckboxTheme CheckBoxTheme;

			public ButtonTheme ChipButton; // Bottom bar -> chip buttons
			public ButtonTheme ChipLibraryChipToggleOff;
			public ButtonTheme ChipLibraryChipToggleOn;
			public ButtonTheme ChipLibraryCollectionToggleOff;
			public ButtonTheme ChipLibraryCollectionToggleOn;

			public InputFieldTheme ChipNameInputField;
			public FontType FontBold;
			public FontType FontRegular;
			public float FontSizeRegular;

			public Color InfoBarCol;

			public ButtonTheme MainMenuButtonTheme; // Main menu buttons
			public Color MenuBackgroundOverlayCol;
			public ButtonTheme MenuButtonTheme; // Bottom bar -> menu button
			public Color MenuPanelCol;
			public ButtonTheme MenuPopupButtonTheme; // Bottom bar -> menu -> popup buttons theme
			public WheelSelectorTheme OptionsWheel;
			public ButtonTheme ProjectSelectionButton; // Main menu -> load project -> unselected project button
			public ButtonTheme ProjectSelectionButtonSelected; // Main menu -> load project -> selected project button
			public ScrollViewTheme ScrollTheme;
			public Color StarredBarCol;
		}
	}
}