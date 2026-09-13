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

		// Circuit labels retain their stable monospace metrics.
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
			Color[] stateLow = Enumerable.Repeat(MakeCol("#FF0000"), 8).ToArray();
			Color[] stateHigh = Enumerable.Repeat(MakeCol("#00B8F0"), 8).ToArray();
			Color[] stateHover = stateLow.Select(c => Brighten(c, 0.075f)).ToArray();
			Color[] stateZero = Enumerable.Repeat(Color.white, 8).ToArray();

			return new ThemeDLS
			{
				SelectionBoxCol = new Color(1, 1, 1, 0.1f),
				SelectionBoxMovingCol = new Color(1, 1, 1, 0.125f),
				SelectionBoxInvalidCol = WithAlpha(MakeCol("#FF4040"), 0.5f),
				SelectionBoxOtherIsInvaldCol = WithAlpha(MakeCol("#D6B77D"), 0.5f),
				StateLowCol = stateLow,
				StateHighCol = stateHigh,
				StateZeroCol = stateZero,
				StateHoverCol = stateHover,
				StateDisconnectedCol = MakeCol("#767E89"),
				DevPinHandle = MakeCol("#34383F"),
				DevPinHandleHighlighted = MakeCol("#00B8F0"),
				PinCol = Color.black,
				PinLabelCol = MakeCol("#AFB5BE"),
				PinHighlightCol = MakeCol("#00B8F0"),
				PinInvalidCol = MakeCol("#FF4040"),
				SevenSegCols = new Color[]
				{
					MakeCol("#17181B"), MakeCol("#00B8F0"), MakeCol("#00B8F0"), // Col A: OFF, ON, HIGHLIGHT
					MakeCol("#17181B"), MakeCol("#00B8F0"), MakeCol("#00B8F0") // Col B: OFF, ON, HIGHLIGHT
				},
				BackgroundCol = MakeCol("#101113"),
				GridCol = Color.black,
			};
		}

		static UIThemeDLS CreateUITheme()
		{
			FontType fontRegular = FontType.OpenSansRegular;
			FontType fontBold = FontType.OpenSansBold;
			float fontSizeRegular = UIThemeLibrary.FontSizeMedium;

			Color primaryText = MakeCol("#FFFFFF");
			Color secondaryText = MakeCol("#AFB5BE");
			Color disabledText = MakeCol("#767E89");

			Color inactiveButtonCol = MakeCol("#1E2024");
			Color inactiveTextol = disabledText;
			Color chipLibaryButtonOff = MakeCol("#282B30");
			Color chipLibaryButtonOn = MakeCol("#00B8F0");
			Color menuPanelCol = MakeCol("#1E2024");

			Color chipLibraryCollectionHighlightCol = MakeCol("#55D2F7");
			Color chipLibraryChipHighlightCol = MakeCol("#00B8F0");

			Color scrollBarCol = MakeCol("#34383F");

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
				ButtonTheme = MakeButtonTheme(fontRegular, MakeCol("#282B30"), MakeCol("#34383F"), MakeCol("#00B8F0"), primaryText, primaryText, primaryText),
				ProjectSelectionButton = MakeButtonTheme(fontRegular, Color.clear, MakeCol("#282B30"), MakeCol("#00B8F0"), primaryText, primaryText, primaryText),
				ProjectSelectionButtonSelected = MakeButtonTheme(fontRegular, MakeCol("#00B8F0"), MakeCol("#55D2F7"), MakeCol("#00B8F0"), MakeCol("#101113"), MakeCol("#101113"), MakeCol("#101113")),
				ChipButton = MakeButtonTheme(fontRegular, MakeCol("#1E2024"), MakeCol("#282B30"), MakeCol("#00B8F0"), primaryText, primaryText, primaryText),
				MainMenuButtonTheme = MakeButtonTheme(fontRegular, MakeCol("#282B30"), MakeCol("#00B8F0"), MakeCol("#00B8F0"), primaryText, primaryText, primaryText),
				MenuButtonTheme = MakeButtonTheme(fontRegular, MakeCol("#1E2024"), MakeCol("#00B8F0"), MakeCol("#00B8F0"), primaryText, primaryText, primaryText),
				MenuPopupButtonTheme = MakeButtonThemeFull(fontRegular, MakeCol("#101113"), MakeCol("#282B30"), MakeCol("#34383F"), inactiveButtonCol, primaryText, primaryText, primaryText, inactiveTextol),

				ChipLibraryCollectionToggleOff = MakeButtonTheme(fontRegular, MakeCol("#282B30"), MakeCol("#34383F"), chipLibraryCollectionHighlightCol, primaryText, primaryText, primaryText),
				ChipLibraryCollectionToggleOn = MakeButtonThemeAuto(fontRegular, chipLibraryCollectionHighlightCol, MakeCol("#101113")),
				ChipLibraryChipToggleOff = MakeButtonTheme(fontRegular, MakeCol("#1E2024"), MakeCol("#34383F"), chipLibraryChipHighlightCol, primaryText, primaryText, primaryText),
				ChipLibraryChipToggleOn = MakeButtonThemeAuto(fontRegular, chipLibraryChipHighlightCol, MakeCol("#101113")),
				
				// Search result themes - neutral background for normal results, accent for selected
				SearchResultNormal = MakeButtonTheme(fontRegular, MakeCol("#1E2024"), MakeCol("#282B30"), MakeCol("#34383F"), primaryText, primaryText, primaryText),
				SearchResultSelected = MakeButtonThemeAuto(fontRegular, chipLibraryChipHighlightCol, MakeCol("#101113")),

				// --- Other stuff ---
				ChipNameInputField = new InputFieldTheme
				{
					font = FontType.JetbrainsMonoBold,
					fontSize = UIThemeLibrary.FontSizeVeryLarge,
					bgCol = MakeCol("#17181B"),
					defaultTextCol = secondaryText,
					textCol = primaryText,
					focusBorderCol = MakeCol("#00B8F0")
				},
				OptionsWheel = new WheelSelectorTheme
				{
					backgroundCol = MakeCol("#1E2024"),
					buttonTheme = MakeButtonTheme(fontBold, MakeCol("#282B30"), MakeCol("#00B8F0"), MakeCol("#00B8F0"), primaryText, primaryText, primaryText),
					textCol = primaryText,
					inactiveTextCol = secondaryText
				},
				ScrollTheme = new ScrollViewTheme
				{
					backgroundCol = MakeCol("#101113"),
					padding = 1,
					scrollBarColBackground = MakeCol("#1E2024"),
					scrollBarColInactive = MakeCol("#282B30"),
					scrollBarColNormal = MakeCol("#34383F"),
					scrollBarColHover = MakeCol("#00B8F0"),
					scrollBarColPressed = MakeCol("#00B8F0"),
					scrollBarWidth = 1
				},
				CheckBoxTheme = new CheckboxTheme
				{
					boxCol = primaryText,
					tickCol = MakeCol("#17181B")
				},
				InfoBarCol = WithAlpha(MakeCol("#101113"), 0.9f),
				StarredBarCol = MakeCol("#282B30")
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
			public Color[] StateZeroCol; // Ternary zero state
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
			public ButtonTheme SearchResultNormal;
			public ButtonTheme SearchResultSelected;

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
