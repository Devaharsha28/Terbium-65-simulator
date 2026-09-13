using System;
using System.Linq;
using DLS.Description;
using DLS.Game;
using DLS.SaveSystem;
using DLS.Simulation;
using Seb.Helpers;
using Seb.Types;
using Seb.Vis;
using Seb.Vis.UI;
using UnityEngine;

namespace DLS.Graphics
{
	// =========================================================================
	// TERBIUM 65 - MAIN MENU LAYOUT
	// =========================================================================

	static class Layout
	{
		// ---------------------------------------------------------------------
		// Global chrome
		// ---------------------------------------------------------------------

		public const float HeaderHeight = 4.6f;
		public const float FooterHeight = 0.8f;

		// ---------------------------------------------------------------------
		// Sidebar
		// ---------------------------------------------------------------------

		public const float SidebarWidth = 17.5f;
		public const float SidebarPadding = 1.45f;

		public const float SidebarSectionGap = 2.4f;

		public const float NavButtonHeight = 2.35f;
		public const float NavButtonSpacing = 0.55f;

		// ---------------------------------------------------------------------
		// Workspace
		// ---------------------------------------------------------------------

		public const float ContentMarginX = 4.6f;
		public const float ContentMarginY = 4.0f;

		public const float SectionSpacing = 3.0f;

		// ---------------------------------------------------------------------
		// Quick-start cards
		// ---------------------------------------------------------------------

		public const float CardHeight = 8.2f;
		public const float CardSpacing = 2.0f;

		public const float CardPaddingX = 1.7f;
		public const float CardTitleOffsetY = 1.65f;
		public const float CardDescriptionOffsetY = 3.65f;

		// ---------------------------------------------------------------------
		// Recent projects
		// ---------------------------------------------------------------------

		public const float ProjectRowHeight = 2.8f;
		public const float ProjectRowSpacing = 0.45f;
		public const float ProjectRowPaddingX = 1.15f;

		// ---------------------------------------------------------------------
		// Header
		// ---------------------------------------------------------------------

		public const float HeaderPaddingX = 2.0f;
		public const float HeaderPaddingY = 0.8f;
	}


	public static partial class MainMenu
	{
		public const int MaxProjectNameLength = 20;

		const bool capitalize = true;

		static MenuScreen activeMenuScreen = MenuScreen.Main;
		static PopupKind activePopup = PopupKind.None;

		static AppSettings EditedAppSettings;

		static readonly UIHandle ID_ProjectNameInput =
			new("MainMenu_ProjectNameInputField");

		static readonly UIHandle ID_DisplayResolutionWheel =
			new("MainMenu_DisplayResolutionWheel");

		static readonly UIHandle ID_FullscreenWheel =
			new("MainMenu_FullscreenWheel");

		static readonly UIHandle ID_ProjectsScrollView =
			new("MainMenu_ProjectsScrollView");


		static readonly string[] SettingsWheelFullScreenOptions =
		{
			"OFF",
			"MAXIMIZED",
			"BORDERLESS",
			"EXCLUSIVE"
		};


		static readonly FullScreenMode[] FullScreenModes =
		{
			FullScreenMode.Windowed,
			FullScreenMode.MaximizedWindow,
			FullScreenMode.FullScreenWindow,
			FullScreenMode.ExclusiveFullScreen
		};


		static readonly string[] SettingsWheelVSyncOptions =
		{
			"DISABLED",
			"ENABLED"
		};


		static readonly Func<string, bool> projectNameValidator =
			ProjectNameValidator;


		static readonly UI.ScrollViewDrawContentFunc loadProjectScrollViewDrawer =
			DrawAllProjectsInScrollView;


		static readonly string[] openProjectButtonNames =
		{
			FormatButtonString("Back"),
			FormatButtonString("Delete"),
			FormatButtonString("Duplicate"),
			FormatButtonString("Rename"),
			FormatButtonString("Open")
		};


		static readonly Vector2Int[] Resolutions =
		{
			new(960, 540),
			new(1280, 720),
			new(1920, 1080),
			new(2560, 1440)
		};


		static readonly string[] ResolutionNames =
			Resolutions
				.Select(r => ResolutionToString(r))
				.ToArray();


		static readonly string[] FullScreenResName =
			Resolutions
				.Select(r => ResolutionToString(Main.FullScreenResolution))
				.ToArray();


		static readonly string[] settingsButtonGroupNames =
		{
			"EXIT",
			"APPLY"
		};


		static readonly bool[] settingsButtonGroupStates =
			new bool[settingsButtonGroupNames.Length];


		static readonly bool[] openProjectButtonStates =
			new bool[openProjectButtonNames.Length];


		static ProjectDescription[] allProjectDescriptions;
		static string[] allProjectNames;

		static (bool compatible, string message)[] projectCompatibilities;

		static int selectedProjectIndex;


		static readonly string authorString =
			"Terbium 65 • Ternary Logic Design Environment";


		static readonly string versionString =
			"v1.0.0";


		static string SelectedProjectName =>
			allProjectDescriptions[selectedProjectIndex].ProjectName;


		static string FormatButtonString(string s) =>
			capitalize ? s.ToUpper() : s;


		// =========================================================================
		// PALETTE
		// =========================================================================

		static class Palette
		{
			// Resolve semantic values at draw time so the main menu and editor share
			// the same palette, including a user's saved custom theme.
			static ThemePalette Active => ThemeManager.ActivePalette;
			public static Color Background => ThemePalette.Parse(Active.Background);
			public static Color Surface => ThemePalette.Parse(Active.Workspace);
			public static Color SurfaceElevated => ThemePalette.Parse(Active.Panel);
			public static Color SurfaceHover => ThemePalette.Parse(Active.PanelElevated);
			public static Color Border => ThemePalette.Parse(Active.Border);
			public static Color BorderSubtle => Color.Lerp(Background, Border, 0.55f);
			public static Color TextPrimary => ThemePalette.Parse(Active.TextPrimary);
			public static Color TextSecondary => ThemePalette.Parse(Active.TextSecondary);
			public static Color TextTertiary => Color.Lerp(ActiveTextDisabled, TextSecondary, 0.38f);
			public static Color TextDisabled => ActiveTextDisabled;
			static Color ActiveTextDisabled => ThemePalette.Parse(Active.TextDisabled);
			public static Color AccentBlue => ThemePalette.Parse(Active.Accent);
			public static Color AccentRed => ThemePalette.Parse(Active.Error);
			public static Color AccentWhite => ThemePalette.Parse(Active.TextPrimary);
			public static Color Accent => ThemePalette.Parse(Active.Accent);
			public static Color Overlay => new Color(0f, 0f, 0f, 0.78f);
		}


		// =========================================================================
		// NAVIGATION THEME
		// =========================================================================

		static ButtonTheme GetNavButtonTheme(
			DrawSettings.UIThemeDLS theme,
			bool isSelected = false)
		{
			return new ButtonTheme
			{
				font = theme.FontRegular,

				fontSize =
					theme.FontSizeRegular * 0.96f,

				textCols =
					new ButtonTheme.StateCols(
						isSelected
							? Palette.TextPrimary
							: Palette.TextSecondary,

						Palette.TextPrimary,
						Palette.TextPrimary,
						Palette.TextDisabled
					),

				buttonCols =
					new ButtonTheme.StateCols(
						isSelected
							? Palette.SurfaceElevated
							: Color.clear,

						Palette.SurfaceHover,
						Palette.SurfaceHover,
						Color.clear
					),

				paddingScale = Vector2.zero
			};
		}


		// =========================================================================
		// MAIN DRAW
		// =========================================================================

		public static void Draw()
		{
			Simulator.UpdateInPausedState();


			if (
				KeyboardShortcuts.CancelShortcutTriggered &&
				activePopup == PopupKind.None &&
				activeMenuScreen != MenuScreen.Main
			)
			{
				BackToMain();
			}


			UI.DrawFullscreenPanel(
				Palette.Background
			);


			if (activeMenuScreen != MenuScreen.Main)
			{
				DrawHeader();
				DrawFooter();
			}


			switch (activeMenuScreen)
			{
				case MenuScreen.Main:
					DrawMainScreen();
					break;

				case MenuScreen.LoadProject:
					DrawLoadProjectScreen();
					break;

				case MenuScreen.Settings:
					DrawSettingsScreen();
					break;

				case MenuScreen.About:
					DrawAboutScreen();
					break;

				case MenuScreen.ThemeEditor:

					if (ThemeEditorMenu.Draw(UI.Centre))
					{
						activeMenuScreen =
							MenuScreen.Settings;
					}

					break;
			}


			switch (activePopup)
			{
				case PopupKind.DeleteConfirmation:
					DrawDeleteProjectConfirmationPopup();
					break;

				case PopupKind.NamePopup_RenameProject:
				case PopupKind.NamePopup_DuplicateProject:
				case PopupKind.NamePopup_NewProject:
					DrawNamePopup();
					break;
			}
		}


		public static void OnMenuOpened()
		{
			activeMenuScreen =
				MenuScreen.Main;

			activePopup =
				PopupKind.None;

			selectedProjectIndex =
				-1;
		}


		// =========================================================================
		// MAIN SCREEN
		// =========================================================================

		static void DrawMainScreen()
		{
			RefreshLoadedProjects();
			using (UI.BeginDisabledScope(activePopup != PopupKind.None))
				DrawHome();
		}


		// =========================================================================
		// SIDEBAR
		// =========================================================================

		static void DrawSidebar(
			DrawSettings.UIThemeDLS theme)
		{
			float sidebarHeight =
				UI.Height -
				Layout.HeaderHeight -
				Layout.FooterHeight;


			UI.DrawPanel(
				new Vector2(
					0,
					Layout.FooterHeight
				),
				new Vector2(
					Layout.SidebarWidth,
					sidebarHeight
				),
				Palette.Surface,
				Anchor.BottomLeft
			);


			UI.DrawLine(
				new Vector2(
					Layout.SidebarWidth,
					Layout.FooterHeight
				),
				new Vector2(
					Layout.SidebarWidth,
					UI.Height -
					Layout.HeaderHeight
				),
				0.07f,
				Palette.Border
			);


			float navX =
				Layout.SidebarPadding;


			float navWidth =
				Layout.SidebarWidth -
				Layout.SidebarPadding * 2f;


			// -----------------------------------------------------------------
			// PROJECT
			// -----------------------------------------------------------------

			float projectLabelY =
				UI.Height -
				Layout.HeaderHeight -
				2.0f;


			DrawSidebarLabel(
				"PROJECT",
				theme,
				navX,
				projectLabelY
			);


			float newProjectY =
				projectLabelY -
				1.55f;


			bool newClicked =
				UI.Button(
					"New Project",
					GetNavButtonTheme(theme, true),
					new Vector2(
						navX,
						newProjectY
					),
					new Vector2(
						navWidth,
						Layout.NavButtonHeight
					),
					true,
					false,
					false,
					Anchor.TopLeft,
					true,
					1.0f
				);


			if (
				newClicked ||
				KeyboardShortcuts.MainMenu_NewProjectShortcutTriggered
			)
			{
				activePopup =
					PopupKind.NamePopup_NewProject;
			}


			float openProjectY =
				newProjectY -
				Layout.NavButtonHeight -
				Layout.NavButtonSpacing;


			bool openClicked =
				UI.Button(
					"Open Project",
					GetNavButtonTheme(theme),
					new Vector2(
						navX,
						openProjectY
					),
					new Vector2(
						navWidth,
						Layout.NavButtonHeight
					),
					true,
					false,
					false,
					Anchor.TopLeft,
					true,
					1.0f
				);


			if (
				openClicked ||
				KeyboardShortcuts.MainMenu_OpenProjectShortcutTriggered
			)
			{
				selectedProjectIndex =
					-1;

				activeMenuScreen =
					MenuScreen.LoadProject;
			}


			float projectDividerY =
				openProjectY -
				Layout.NavButtonHeight -
				0.95f;


			DrawSidebarDivider(
				navX,
				projectDividerY
			);


			// -----------------------------------------------------------------
			// APPLICATION
			// -----------------------------------------------------------------

			float applicationLabelY =
				projectDividerY -
				1.35f;


			DrawSidebarLabel(
				"APPLICATION",
				theme,
				navX,
				applicationLabelY
			);


			float settingsY =
				applicationLabelY -
				1.55f;


			bool settingsClicked =
				UI.Button(
					"Settings",
					GetNavButtonTheme(theme),
					new Vector2(
						navX,
						settingsY
					),
					new Vector2(
						navWidth,
						Layout.NavButtonHeight
					),
					true,
					false,
					false,
					Anchor.TopLeft,
					true,
					1.0f
				);


			if (
				settingsClicked ||
				KeyboardShortcuts.MainMenu_SettingsShortcutTriggered
			)
			{
				EditedAppSettings =
					Main.ActiveAppSettings;

				activeMenuScreen =
					MenuScreen.Settings;

				OnSettingsMenuOpened();
			}


			float aboutY =
				settingsY -
				Layout.NavButtonHeight -
				Layout.NavButtonSpacing;


			bool aboutClicked =
				UI.Button(
					"About",
					GetNavButtonTheme(theme),
					new Vector2(
						navX,
						aboutY
					),
					new Vector2(
						navWidth,
						Layout.NavButtonHeight
					),
					true,
					false,
					false,
					Anchor.TopLeft,
					true,
					1.0f
				);


			if (aboutClicked)
			{
				activeMenuScreen =
					MenuScreen.About;
			}


			// -----------------------------------------------------------------
			// QUIT
			// -----------------------------------------------------------------

			float quitY =
				Layout.FooterHeight +
				Layout.NavButtonHeight +
				0.65f;


			float quitDividerY =
				quitY +
				0.95f;


			DrawSidebarDivider(
				navX,
				quitDividerY
			);


			bool quitClicked =
				UI.Button(
					"Quit",
					GetNavButtonTheme(theme),
					new Vector2(
						navX,
						quitY
					),
					new Vector2(
						navWidth,
						Layout.NavButtonHeight
					),
					true,
					false,
					false,
					Anchor.TopLeft,
					true,
					1.0f
				);


			if (
				quitClicked ||
				KeyboardShortcuts.MainMenu_QuitShortcutTriggered
			)
			{
				Quit();
			}
		}


		static void DrawSidebarLabel(
			string text,
			DrawSettings.UIThemeDLS theme,
			float x,
			float y)
		{
			UI.DrawText(
				text,
				theme.FontRegular,
				theme.FontSizeRegular * 0.70f,
				new Vector2(
					x + 0.15f,
					y
				),
				Anchor.TopLeft,
				Palette.TextTertiary
			);
		}


		static void DrawSidebarDivider(
			float navX,
			float y)
		{
			UI.DrawLine(
				new Vector2(
					navX + 0.15f,
					y
				),
				new Vector2(
					Layout.SidebarWidth -
					navX -
					0.15f,
					y
				),
				0.045f,
				Palette.BorderSubtle
			);
		}


		// =========================================================================
		// MAIN WORKSPACE
		// =========================================================================

		static void DrawMainWorkspace(
			DrawSettings.UIThemeDLS theme)
		{
			float workspaceLeft =
				Layout.SidebarWidth +
				Layout.ContentMarginX;


			float workspaceRight =
				UI.Width -
				Layout.ContentMarginX;


			float workspaceTop =
				UI.Height -
				Layout.HeaderHeight -
				Layout.ContentMarginY;


			float workspaceWidth =
				workspaceRight -
				workspaceLeft;


			Vector2 contentPos =
				new(
					workspaceLeft,
					workspaceTop
				);


			// -----------------------------------------------------------------
			// HERO
			// -----------------------------------------------------------------

			UI.DrawText(
				"Design logic, clearly.",
				theme.FontBold,
				theme.FontSizeRegular * 2.05f,
				contentPos,
				Anchor.TopLeft,
				Palette.TextPrimary
			);


			contentPos.y -= 2.7f;


			UI.DrawText(
				"A focused workspace for creating and testing ternary circuits.",
				theme.FontRegular,
				theme.FontSizeRegular * 1.00f,
				contentPos,
				Anchor.TopLeft,
				Palette.TextSecondary
			);


			// -----------------------------------------------------------------
			// QUICK START
			// -----------------------------------------------------------------

			contentPos.y -= 3.5f;


			UI.DrawText(
				"QUICK START",
				theme.FontRegular,
				theme.FontSizeRegular * 0.72f,
				contentPos,
				Anchor.TopLeft,
				Palette.TextTertiary
			);


			contentPos.y -= 1.85f;


			float maxContentWidth =
				60.0f;


			float effectiveWidth =
				Mathf.Min(
					workspaceWidth,
					maxContentWidth
				);


			float cardWidth =
				(effectiveWidth -
				Layout.CardSpacing) / 2f;


			float cardLeft =
				workspaceLeft;


			float cardRight =
				cardLeft +
				cardWidth +
				Layout.CardSpacing;


			// -----------------------------------------------------------------
			// NEW PROJECT
			// -----------------------------------------------------------------

			bool newCardClicked =
				DrawActionCard(
					theme,
					new Vector2(
						cardLeft,
						contentPos.y
					),
					new Vector2(
						cardWidth,
						Layout.CardHeight
					),
					"New Project",
					"Start with a blank workspace\nand build your circuit."
				);


			if (newCardClicked)
			{
				activePopup =
					PopupKind.NamePopup_NewProject;
			}


			// -----------------------------------------------------------------
			// OPEN PROJECT
			// -----------------------------------------------------------------

			bool openCardClicked =
				DrawActionCard(
					theme,
					new Vector2(
						cardRight,
						contentPos.y
					),
					new Vector2(
						cardWidth,
						Layout.CardHeight
					),
					"Open Project",
					"Continue where you left off\nwith an existing project."
				);


			if (openCardClicked)
			{
				selectedProjectIndex =
					-1;

				activeMenuScreen =
					MenuScreen.LoadProject;
			}


			// -----------------------------------------------------------------
			// RECENT PROJECTS
			// -----------------------------------------------------------------

			contentPos.y -=
				Layout.CardHeight +
				3.8f;


			UI.DrawText(
				"RECENT PROJECTS",
				theme.FontRegular,
				theme.FontSizeRegular * 0.72f,
				contentPos,
				Anchor.TopLeft,
				Palette.TextTertiary
			);


			contentPos.y -= 1.8f;


			if (
				allProjectDescriptions == null ||
				allProjectDescriptions.Length == 0
			)
			{
				UI.DrawText(
					"No recent projects.",
					theme.FontRegular,
					theme.FontSizeRegular * 0.76f,
					contentPos,
					Anchor.TopLeft,
					Palette.TextDisabled
				);
			}
			else
			{
				float rowY =
					contentPos.y;


				float minBottom =
					Layout.FooterHeight +
					1.0f;


				int maxVisibleRows =
					Mathf.Max(
						1,
						Mathf.FloorToInt(
							(rowY - minBottom) /
							(
								Layout.ProjectRowHeight +
								Layout.ProjectRowSpacing
							)
						)
					);


				int count =
					Mathf.Min(
						allProjectDescriptions.Length,
						maxVisibleRows
					);


				for (int i = 0; i < count; i++)
				{
					ProjectDescription desc =
						allProjectDescriptions[i];


					Vector2 rowPos =
						new(
							workspaceLeft,
							rowY
						);


					Vector2 rowSize =
						new(
							effectiveWidth,
							Layout.ProjectRowHeight
						);


					bool rowClicked =
						DrawProjectRow(
							theme,
							rowPos,
							rowSize,
							desc.ProjectName
						);


					if (rowClicked)
					{
						Main.CreateOrLoadProject(
							desc.ProjectName,
							string.Empty
						);
					}


					rowY -=
						Layout.ProjectRowHeight +
						Layout.ProjectRowSpacing;
				}
			}
		}


		// =========================================================================
		// ACTION CARD
		// =========================================================================

		static bool DrawActionCard(
			DrawSettings.UIThemeDLS theme,
			Vector2 pos,
			Vector2 size,
			string title,
			string description)
		{
			ButtonTheme cardBtnTheme =
				new()
				{
					font = theme.FontRegular,

					fontSize =
						theme.FontSizeRegular,

					textCols =
						new ButtonTheme.StateCols(
							Color.clear,
							Color.clear,
							Color.clear,
							Color.clear
						),

					buttonCols =
						new ButtonTheme.StateCols(
							Color.clear,
							Color.clear,
							Color.clear,
							Color.clear
						),

					paddingScale = Vector2.zero
				};


			Bounds2D cardBounds =
				Bounds2D.CreateFromTopLeftAndSize(
					pos,
					size
				);


			bool mouseOver =
				UI.MouseInsideBounds(cardBounds);


			Color bgCol =
				mouseOver
					? Palette.SurfaceHover
					: Palette.SurfaceElevated;


			// Keep the cyan accent extremely subtle.
			Color borderCol =
				mouseOver
					? Palette.AccentBlue
					: Palette.Border;


			// -----------------------------------------------------------------
			// PANEL
			// -----------------------------------------------------------------

			UI.DrawPanel(
				pos,
				size,
				bgCol,
				Anchor.TopLeft
			);


			// A restrained full border makes the cards feel intentional without
			// resorting to shadows or gradients.
			UI.DrawLine(pos, pos + Vector2.right * size.x, 0.045f, borderCol);
			UI.DrawLine(pos + Vector2.right * size.x, pos + new Vector2(size.x, -size.y), 0.045f, borderCol);

			// Identity accent.
			UI.DrawLine(
				pos + new Vector2(
					0,
					-0.08f
				),
				pos + new Vector2(
					0,
					-size.y + 0.08f
				),
				mouseOver
					? 0.10f
					: 0.055f,
				borderCol
			);


			// Bottom edge.
			UI.DrawLine(
				pos + new Vector2(
					0,
					-size.y
				),
				pos + new Vector2(
					size.x,
					-size.y
				),
				0.045f,
				mouseOver
					? Palette.Border
					: Palette.BorderSubtle
			);


			// -----------------------------------------------------------------
			// TITLE
			// -----------------------------------------------------------------

			Vector2 titlePos =
				pos +
				new Vector2(
					Layout.CardPaddingX,
					-Layout.CardTitleOffsetY
				);


			UI.DrawText(
				title,
				theme.FontBold,
				theme.FontSizeRegular * 1.12f,
				titlePos,
				Anchor.TopLeft,
				Palette.TextPrimary
			);


			// -----------------------------------------------------------------
			// DESCRIPTION
			// -----------------------------------------------------------------

			Vector2 descPos =
				pos +
				new Vector2(
					Layout.CardPaddingX,
					-Layout.CardDescriptionOffsetY
				);


			UI.DrawText(
				description,
				theme.FontRegular,
				theme.FontSizeRegular * 0.82f,
				descPos,
				Anchor.TopLeft,
				Palette.TextSecondary
			);


			UI.DrawText(
				title == "New Project" ? "CREATE PROJECT" : "BROWSE PROJECTS",
				theme.FontBold,
				theme.FontSizeRegular * 0.70f,
				pos + new Vector2(Layout.CardPaddingX, -size.y + 1.15f),
				Anchor.BottomLeft,
				mouseOver ? Palette.Accent : Palette.TextPrimary
			);


			return UI.Button(
				"",
				cardBtnTheme,
				pos,
				size,
				true,
				false,
				false,
				Anchor.TopLeft
			);
		}


		// =========================================================================
		// PROJECT ROW
		// =========================================================================

		static bool DrawProjectRow(
			DrawSettings.UIThemeDLS theme,
			Vector2 pos,
			Vector2 size,
			string projectName)
		{
			ButtonTheme rowBtnTheme =
				new()
				{
					font = theme.FontRegular,

					fontSize =
						theme.FontSizeRegular,

					textCols =
						new ButtonTheme.StateCols(
							Color.clear,
							Color.clear,
							Color.clear,
							Color.clear
						),

					buttonCols =
						new ButtonTheme.StateCols(
							Color.clear,
							Palette.SurfaceHover,
							Palette.SurfaceHover,
							Color.clear
						),

					paddingScale = Vector2.zero
				};


			Bounds2D rowBounds =
				Bounds2D.CreateFromTopLeftAndSize(
					pos,
					size
				);


			bool mouseOver =
				UI.MouseInsideBounds(rowBounds);


			if (mouseOver)
			{
				UI.DrawPanel(
					pos,
					size,
					Palette.SurfaceElevated,
					Anchor.TopLeft
				);
			}


			// Bottom divider.
			UI.DrawLine(
				pos + new Vector2(
					0,
					-size.y
				),
				pos + new Vector2(
					size.x,
					-size.y
				),
				0.04f,
				Palette.BorderSubtle
			);


			// Project name.
			Vector2 namePos =
				pos +
				new Vector2(
					Layout.ProjectRowPaddingX,
					-size.y / 2f
				);


			UI.DrawText(
				projectName,
				theme.FontRegular,
				theme.FontSizeRegular * 0.92f,
				namePos,
				Anchor.CentreLeft,
				mouseOver
					? Palette.TextPrimary
					: Palette.TextSecondary
			);


			return UI.Button(
				"",
				rowBtnTheme,
				pos,
				size,
				true,
				false,
				false,
				Anchor.TopLeft
			);
		}


		// =========================================================================
		// LOAD PROJECT
		// =========================================================================

		static void DrawLoadProjectScreen()
		{
			const int backButtonIndex = 0;
			const int deleteButtonIndex = 1;
			const int duplicateButtonIndex = 2;
			const int renameButtonIndex = 3;
			const int openButtonIndex = 4;


			DrawSettings.UIThemeDLS theme =
				DrawSettings.ActiveUITheme;


			RefreshLoadedProjects();

			DrawSidebarWithBack(theme);


			float workspaceLeft =
				Layout.SidebarWidth +
				Layout.ContentMarginX;


			float workspaceRight =
				UI.Width -
				Layout.ContentMarginX;


			float workspaceTop =
				UI.Height -
				Layout.HeaderHeight -
				Layout.ContentMarginY;


			float workspaceWidth =
				workspaceRight -
				workspaceLeft;


			Vector2 contentPos =
				new(
					workspaceLeft,
					workspaceTop
				);


			UI.DrawText(
				"Open Project",
				theme.FontBold,
				theme.FontSizeRegular * 1.16f,
				contentPos,
				Anchor.TopLeft,
				Palette.TextPrimary
			);


			contentPos.y -= 2.0f;


			Vector2 projectsScrollSize =
				new(
					workspaceWidth,
					14f
				);


			UI.DrawScrollView(
				ID_ProjectsScrollView,
				contentPos,
				projectsScrollSize,
				Anchor.TopLeft,
				theme.ScrollTheme,
				loadProjectScrollViewDrawer
			);


			ButtonTheme buttonTheme =
				theme.MainMenuButtonTheme;


			bool projectSelected =
				selectedProjectIndex >= 0 &&
				selectedProjectIndex <
				allProjectDescriptions.Length;


			bool compatibleProject =
				projectSelected &&
				projectCompatibilities[
					selectedProjectIndex
				].compatible;


			for (
				int i = 0;
				i < openProjectButtonStates.Length;
				i++
			)
			{
				bool buttonEnabled =
					activePopup == PopupKind.None &&
					(
						compatibleProject ||
						i == backButtonIndex ||
						(
							i == deleteButtonIndex &&
							projectSelected
						)
					);


				openProjectButtonStates[i] =
					buttonEnabled;
			}


			Vector2 buttonRegionPos =
				UI.PrevBounds.BottomLeft +
				Vector2.down * 1.0f;


			int buttonIndex =
				UI.HorizontalButtonGroup(
					openProjectButtonNames,
					openProjectButtonStates,
					buttonTheme,
					buttonRegionPos,
					UI.PrevBounds.Width,
					UILayoutHelper.DefaultSpacing,
					0,
					Anchor.TopLeft
				);


			if (
				projectSelected &&
				!compatibleProject
			)
			{
				Vector2 errorMessagePos =
					UI.PrevBounds.BottomLeft +
					Vector2.down * 0.7f;


				UI.DrawText(
					projectCompatibilities[
						selectedProjectIndex
					].message,
					buttonTheme.font,
					buttonTheme.fontSize * 0.78f,
					errorMessagePos,
					Anchor.TopLeft,
					Palette.AccentRed
				);
			}


			if (buttonIndex == backButtonIndex)
			{
				BackToMain();
			}
			else if (buttonIndex == deleteButtonIndex)
			{
				activePopup =
					PopupKind.DeleteConfirmation;
			}
			else if (buttonIndex == duplicateButtonIndex)
			{
				activePopup =
					PopupKind.NamePopup_DuplicateProject;
			}
			else if (buttonIndex == renameButtonIndex)
			{
				activePopup =
					PopupKind.NamePopup_RenameProject;
			}
			else if (buttonIndex == openButtonIndex)
			{
				Main.CreateOrLoadProject(
					SelectedProjectName,
					string.Empty
				);
			}
		}


		// =========================================================================
		// SIDEBAR WITH BACK
		// =========================================================================

		static void DrawSidebarWithBack(
			DrawSettings.UIThemeDLS theme)
		{
			float sidebarHeight =
				UI.Height -
				Layout.HeaderHeight -
				Layout.FooterHeight;


			UI.DrawPanel(
				new Vector2(
					0,
					Layout.FooterHeight
				),
				new Vector2(
					Layout.SidebarWidth,
					sidebarHeight
				),
				Palette.Surface,
				Anchor.BottomLeft
			);


			UI.DrawLine(
				new Vector2(
					Layout.SidebarWidth,
					Layout.FooterHeight
				),
				new Vector2(
					Layout.SidebarWidth,
					UI.Height -
					Layout.HeaderHeight
				),
				0.07f,
				Palette.Border
			);


			ButtonTheme navTheme =
				GetNavButtonTheme(theme);


			float currentY =
				UI.Height -
				Layout.HeaderHeight -
				1.9f;


			float navWidth =
				Layout.SidebarWidth -
				Layout.SidebarPadding * 2f;


			float navX =
				Layout.SidebarPadding;


			bool backClicked =
				UI.Button(
					"← Back",
					navTheme,
					new Vector2(
						navX,
						currentY
					),
					new Vector2(
						navWidth,
						Layout.NavButtonHeight
					),
					true,
					false,
					false,
					Anchor.TopLeft,
					true,
					1.0f
				);


			if (backClicked)
			{
				BackToMain();
			}
		}


		// =========================================================================
		// PROJECT VALIDATION
		// =========================================================================

		static bool ProjectNameValidator(
			string inputString)
		{
			return
				inputString.Length <= 20 &&
				!SaveUtils.NameContainsForbiddenChar(
					inputString
				);
		}


		// =========================================================================
		// PROJECT LIST
		// =========================================================================

		static void DrawAllProjectsInScrollView(
			Vector2 topLeft,
			float width,
			bool isLayoutPass)
		{
			float spacing =
				0.3f;


			bool enabled =
				activePopup == PopupKind.None;


			for (
				int i = 0;
				i < allProjectDescriptions.Length;
				i++
			)
			{
				ProjectDescription desc =
					allProjectDescriptions[i];


				bool selected =
					i == selectedProjectIndex;


				ButtonTheme buttonTheme =
					selected
						? DrawSettings.ActiveUITheme.ProjectSelectionButtonSelected
						: DrawSettings.ActiveUITheme.ProjectSelectionButton;


				if (!projectCompatibilities[i].compatible)
				{
					buttonTheme.textCols.normal.a =
						0.5f;
				}


				if (
					UI.Button(
						desc.ProjectName,
						buttonTheme,
						topLeft,
						new Vector2(
							width,
							Layout.ProjectRowHeight
						),
						enabled,
						false,
						false,
						Anchor.TopLeft,
						true,
						0.8f
					)
				)
				{
					selectedProjectIndex =
						i;
				}


				topLeft =
					UI.PrevBounds.BottomLeft +
					Vector2.down * spacing;
			}
		}


		static void RefreshLoadedProjects()
		{
			allProjectDescriptions =
				Loader.LoadAllProjectDescriptions();


			allProjectNames =
				allProjectDescriptions
					.Select(d => d.ProjectName)
					.ToArray();


			projectCompatibilities =
				allProjectDescriptions
					.Select(d => CanOpenProject(d))
					.ToArray();
		}


		static (bool canOpen, string failureReason)
			CanOpenProject(
				ProjectDescription projectDescription)
		{
			try
			{
				Main.Version earliestCompatible =
					Main.Version.Parse(
						projectDescription
							.DLSVersion_EarliestCompatible
					);


				Main.Version currentVersion =
					Main.DLSVersion;


				bool canOpen =
					currentVersion.ToInt() >=
					earliestCompatible.ToInt();


				string failureReason =
					canOpen
						? string.Empty
						: $"This project requires version {earliestCompatible} or later.";


				return (
					canOpen,
					failureReason
				);
			}
			catch
			{
				Debug.Log(
					"Incompatible project: " +
					projectDescription.ProjectName
				);


				return (
					false,
					"Unrecognized project format"
				);
			}
		}


		// =========================================================================
		// NAVIGATION
		// =========================================================================

		static void BackToMain()
		{
			UI.GetInputFieldState(
				ID_ProjectNameInput
			).ClearText();


			activeMenuScreen =
				MenuScreen.Main;


			activePopup =
				PopupKind.None;
		}


		// =========================================================================
		// SETTINGS
		// =========================================================================

		static void OnSettingsMenuOpened()
		{
			WheelSelectorState resolutionWheelState =
				UI.GetWheelSelectorState(
					ID_DisplayResolutionWheel
				);


			int closestMatchError =
				int.MaxValue;


			for (
				int i = 0;
				i < Resolutions.Length;
				i++
			)
			{
				int matchError =
					Mathf.Min(
						Mathf.Abs(
							Screen.width -
							Resolutions[i].x
						),
						Mathf.Abs(
							Screen.height -
							Resolutions[i].y
						)
					);


				if (matchError < closestMatchError)
				{
					closestMatchError =
						matchError;

					resolutionWheelState.index =
						i;
				}
			}


			WheelSelectorState fullscreenWheelState =
				UI.GetWheelSelectorState(
					ID_FullscreenWheel
				);


			for (
				int i = 0;
				i < FullScreenModes.Length;
				i++
			)
			{
				if (
					Screen.fullScreenMode ==
					FullScreenModes[i]
				)
				{
					fullscreenWheelState.index =
						i;

					break;
				}
			}
		}


		static void DrawSettingsScreen()
		{
			var theme = DrawSettings.ActiveUITheme;
			DrawSidebarWithBack(theme);
			float left = Layout.SidebarWidth + Layout.ContentMarginX;
			float width = UI.Width - left - Layout.ContentMarginX;
			float top = UI.Height - Layout.HeaderHeight - Layout.ContentMarginY;
			UI.DrawText("Settings", theme.FontBold, theme.FontSizeRegular * 1.16f,
				new Vector2(left, top), Anchor.TopLeft, Palette.TextPrimary);

			// Reserve the title's actual height before starting the panel.
			float panelTop = UI.PrevBounds.Bottom - 2f;
			const float padding = 1.5f;
			const float rowHeight = 4.6f;
			const float controlHeight = 3f;
			float controlWidth = Mathf.Min(24f, width * 0.48f);
			float controlRight = left + width - padding;
			float panelHeight = padding * 2 + rowHeight * 4;
			UI.DrawPanel(new Vector2(left, panelTop), new Vector2(width, panelHeight),
				Palette.Surface, Anchor.TopLeft);
			Vector2 wheelSize = new(controlWidth, controlHeight);
			Vector2 Row(int index) => new(controlRight, panelTop - padding - rowHeight * (index + 0.5f));

			string[] labels = { "Resolution", "Fullscreen", "VSync", "Theme" };
			for (int i = 0; i < labels.Length; i++)
			{
				UI.DrawText(labels[i], theme.FontRegular, theme.FontSizeRegular,
					new Vector2(left + padding, Row(i).y), Anchor.TextCentreLeft, Palette.TextPrimary);
				if (i < labels.Length - 1)
				{
					float dividerY = panelTop - padding - rowHeight * (i + 1);
					UI.DrawLine(new Vector2(left + padding, dividerY),
						new Vector2(controlRight, dividerY), 0.035f, Palette.BorderSubtle);
				}
			}

			bool resEnabled = EditedAppSettings.fullscreenMode == FullScreenMode.Windowed;
			int resIndex = UI.WheelSelector(ID_DisplayResolutionWheel,
				resEnabled ? ResolutionNames : FullScreenResName,
				Row(0), wheelSize, theme.OptionsWheel, Anchor.CentreRight, enabled: resEnabled);
			if (resEnabled)
			{
				EditedAppSettings.ResolutionX = Resolutions[resIndex].x;
				EditedAppSettings.ResolutionY = Resolutions[resIndex].y;
			}

			int mode = UI.WheelSelector(ID_FullscreenWheel, SettingsWheelFullScreenOptions,
				Row(1), wheelSize, theme.OptionsWheel, Anchor.CentreRight);
			EditedAppSettings.fullscreenMode = FullScreenModes[mode];
			int vsync = UI.WheelSelector(EditedAppSettings.VSyncEnabled ? 1 : 0,
				SettingsWheelVSyncOptions, Row(2), wheelSize, theme.OptionsWheel, Anchor.CentreRight);
			EditedAppSettings.VSyncEnabled = vsync == 1;
			if (UI.Button("Edit theme", theme.MenuButtonTheme, Row(3), wheelSize,
				true, false, false, Anchor.CentreRight))
			{
				ThemeEditorMenu.OnMenuOpened();
				activeMenuScreen = MenuScreen.ThemeEditor;
			}

			// Action placement is independent of whichever control was drawn last.
			Vector2 actionPos = new(left, panelTop - panelHeight - 1.5f);
			Vector2 actionSize = new((width - 1f) / 2, 3.4f);
			if (UI.Button("Back", theme.MainMenuButtonTheme, actionPos, actionSize,
				true, false, false, Anchor.TopLeft)) BackToMain();
			if (UI.Button("Apply", theme.MainMenuButtonTheme,
				actionPos + Vector2.right * (actionSize.x + 1f), actionSize,
				true, false, false, Anchor.TopLeft))
				Main.SaveAndApplyAppSettings(EditedAppSettings);
		}


		static void DrawSettingsLabel(
			string text,
			DrawSettings.UIThemeDLS theme,
			Vector2 position)
		{
			UI.DrawText(
				text,
				theme.FontRegular,
				theme.FontSizeRegular * 0.84f,
				position,
				Anchor.TopLeft,
				Palette.TextPrimary
			);
		}


		// =========================================================================
		// NAME POPUP
		// =========================================================================

		static void DrawNamePopup()
		{
			DrawSettings.UIThemeDLS theme =
				DrawSettings.ActiveUITheme;


			UI.StartOverlayLayer();


			UI.DrawFullscreenPanel(
				Palette.Overlay
			);


			using (UI.BeginBoundsScope(true))
			{
				Draw.ID panelID =
					UI.ReservePanel();


				InputFieldTheme inputTheme =
					theme.ChipNameInputField;


				Vector2 charSize =
					UI.CalculateTextSize(
						"M",
						inputTheme.fontSize,
						inputTheme.font
					);


				Vector2 padding =
					new(
						2,
						2
					);


				Vector2 inputFieldSize =
					new Vector2(
						charSize.x *
						MaxProjectNameLength,
						charSize.y
					) +
					padding * 2;


				InputFieldState state =
					UI.InputField(
						ID_ProjectNameInput,
						inputTheme,
						UI.Centre,
						inputFieldSize,
						"",
						Anchor.Centre,
						padding.x,
						projectNameValidator,
						true
					);


				string projectName =
					state.text;


				bool validProjectName =
					!string.IsNullOrWhiteSpace(
						projectName
					) &&
					SaveUtils.ValidFileName(
						projectName
					);


				bool projectNameAlreadyExists =
					false;


				foreach (
					string existingProjectName
					in allProjectNames)
				{
					projectNameAlreadyExists |=
						string.Equals(
							projectName,
							existingProjectName,
							StringComparison.CurrentCultureIgnoreCase
						);
				}


				bool canCreateProject =
					validProjectName &&
					!projectNameAlreadyExists;


				Vector2 buttonsRegionSize =
					new(
						inputFieldSize.x,
						5
					);


				Vector2 buttonsRegionCentre =
					UILayoutHelper.CalculateCentre(
						UI.PrevBounds.BottomLeft,
						buttonsRegionSize,
						Anchor.TopLeft
					);


				(Vector2 size, Vector2 centre) layoutCancel =
					UILayoutHelper.HorizontalLayout(
						2,
						0,
						buttonsRegionCentre,
						buttonsRegionSize
					);


				(Vector2 size, Vector2 centre) layoutConfirm =
					UILayoutHelper.HorizontalLayout(
						2,
						1,
						buttonsRegionCentre,
						buttonsRegionSize
					);


				bool cancelButton =
					UI.Button(
						"CANCEL",
						theme.MainMenuButtonTheme,
						layoutCancel.centre,
						new Vector2(
							layoutCancel.size.x,
							0
						),
						true,
						false,
						true
					);


				bool confirmButton =
					UI.Button(
						"CONFIRM",
						theme.MainMenuButtonTheme,
						layoutConfirm.centre,
						new Vector2(
							layoutConfirm.size.x,
							0
						),
						canCreateProject,
						false,
						true
					);


				if (
					cancelButton ||
					KeyboardShortcuts.CancelShortcutTriggered
				)
				{
					state.ClearText();

					activePopup =
						PopupKind.None;
				}


				if (
					confirmButton ||
					KeyboardShortcuts.ConfirmShortcutTriggered
				)
				{
					state.ClearText();


					PopupKind kind =
						activePopup;


					activePopup =
						PopupKind.None;


					OnNamePopupConfirmed(
						kind,
						projectName
					);
				}


				UI.ModifyPanel(
					panelID,
					UI.GetCurrentBoundsScope().Centre,
					UI.GetCurrentBoundsScope().Size +
					Vector2.one * 2,
					theme.MenuPanelCol
				);
			}
		}


		// =========================================================================
		// NAME POPUP ACTION
		// =========================================================================

		static void OnNamePopupConfirmed(
			PopupKind kind,
			string name)
		{
			if (
				kind is
					PopupKind.NamePopup_RenameProject or
					PopupKind.NamePopup_DuplicateProject
			)
			{
				if (
					kind ==
					PopupKind.NamePopup_RenameProject
				)
				{
					Saver.RenameProject(
						SelectedProjectName,
						name
					);
				}


				if (
					kind ==
					PopupKind.NamePopup_DuplicateProject
				)
				{
					Saver.DuplicateProject(
						SelectedProjectName,
						name
					);
				}


				RefreshLoadedProjects();


				selectedProjectIndex =
					0;


				UI.GetScrollbarState(
					ID_ProjectsScrollView
				).scrollY = 0;
			}
			else if (
				kind ==
				PopupKind.NamePopup_NewProject
			)
			{
				Main.CreateOrLoadProject(
					name
				);
			}
		}


		// =========================================================================
		// DELETE POPUP
		// =========================================================================

		static void DrawDeleteProjectConfirmationPopup()
		{
			DrawSettings.UIThemeDLS theme =
				DrawSettings.ActiveUITheme;


			UI.StartOverlayLayer();


			UI.DrawFullscreenPanel(
				Palette.Overlay
			);


			using (UI.BeginBoundsScope(true))
			{
				Draw.ID panelID =
					UI.ReservePanel();


				UI.DrawText(
					"Are you sure you want to delete this project?",
					theme.FontRegular,
					theme.FontSizeRegular,
					UI.Centre,
					Anchor.Centre,
					Palette.TextPrimary
				);


				Vector2 buttonRegionTopLeft =
					UI.PrevBounds.BottomLeft +
					Vector2.down *
					DrawSettings.VerticalButtonSpacing;


				float buttonRegionWidth =
					UI.PrevBounds.Width;


				int buttonIndex =
					UI.HorizontalButtonGroup(
						new[]
						{
							"CANCEL",
							"DELETE"
						},
						theme.MainMenuButtonTheme,
						buttonRegionTopLeft,
						buttonRegionWidth,
						DrawSettings.HorizontalButtonSpacing,
						0,
						Anchor.TopLeft
					);


				UI.ModifyPanel(
					panelID,
					UI.GetCurrentBoundsScope().Centre,
					UI.GetCurrentBoundsScope().Size +
					Vector2.one * 2,
					theme.MenuPanelCol
				);


				if (buttonIndex == 0)
				{
					activePopup =
						PopupKind.None;
				}
				else if (buttonIndex == 1)
				{
					Saver.DeleteProject(
						SelectedProjectName
					);


					selectedProjectIndex =
						-1;


					RefreshLoadedProjects();


					activePopup =
						PopupKind.None;
				}
			}
		}


		// =========================================================================
		// ABOUT
		// =========================================================================

		static void DrawAboutScreen()
		{
			DrawSettings.UIThemeDLS theme =
				DrawSettings.ActiveUITheme;


			DrawSidebarWithBack(theme);


			float workspaceLeft =
				Layout.SidebarWidth +
				Layout.ContentMarginX;


			float workspaceTop =
				UI.Height -
				Layout.HeaderHeight -
				Layout.ContentMarginY;


			Vector2 contentPos =
				new(
					workspaceLeft,
					workspaceTop
				);


			UI.DrawText(
				"About",
				theme.FontBold,
				theme.FontSizeRegular * 1.16f,
				contentPos,
				Anchor.TopLeft,
				Palette.TextPrimary
			);


			contentPos.y -= 2.5f;


			string aboutText =
				"Terbium 65 is a digital logic simulation\n" +
				"environment for designing and experimenting\n" +
				"with ternary circuits and ternary computer\n" +
				"architectures.\n\n" +
				"Originally created by Sebastian Lague\n" +
				"as Digital Logic Sim.\n\n" +
				"Forked and modified by DevaHarsha28.";


			UI.DrawText(
				aboutText,
				theme.FontRegular,
				theme.FontSizeRegular * 0.84f,
				contentPos,
				Anchor.TopLeft,
				Palette.TextSecondary
			);
		}


		// =========================================================================
		// HEADER
		// =========================================================================

		static void DrawHeader()
		{
			DrawSettings.UIThemeDLS theme =
				DrawSettings.ActiveUITheme;


			UI.DrawPanel(
				new Vector2(
					0,
					UI.Height
				),
				new Vector2(
					UI.Width,
					Layout.HeaderHeight
				),
				Palette.Surface,
				Anchor.TopLeft
			);


			UI.DrawLine(
				new Vector2(
					0,
					UI.Height -
					Layout.HeaderHeight
				),
				new Vector2(
					UI.Width,
					UI.Height -
					Layout.HeaderHeight
				),
				0.07f,
				Palette.Border
			);


			float titleLeft =
				Layout.HeaderPaddingX;


			float titleTop =
				UI.Height -
				Layout.HeaderPaddingY;


			// Small identity marker.
			UI.DrawLine(
				new Vector2(
					titleLeft - 0.55f,
					titleTop - 0.05f
				),
				new Vector2(
					titleLeft - 0.55f,
					titleTop - 2.55f
				),
				0.075f,
				Palette.AccentBlue
			);


			// Brand.
			UI.DrawText(
				"TERBIUM 65",
				theme.FontBold,
				theme.FontSizeRegular * 1.08f,
				new Vector2(
					titleLeft,
					titleTop
				),
				Anchor.TopLeft,
				Palette.TextPrimary
			);


			// Subtitle.
			UI.DrawText(
				"Ternary Logic Design Environment",
				theme.FontRegular,
				theme.FontSizeRegular * 0.76f,
				new Vector2(
					titleLeft,
					UI.Height - 2.35f
				),
				Anchor.TopLeft,
				Palette.TextSecondary
			);


			// Version.
			UI.DrawText(
				versionString,
				theme.FontRegular,
				theme.FontSizeRegular * 0.70f,
				new Vector2(
					UI.Width -
					Layout.HeaderPaddingX,
					UI.Height -
					Layout.HeaderHeight / 2f
				),
				Anchor.CentreRight,
				Palette.TextTertiary
			);
		}


		// =========================================================================
		// FOOTER
		// =========================================================================

		static void DrawFooter()
		{
			UI.DrawLine(
				new Vector2(
					0,
					Layout.FooterHeight
				),
				new Vector2(
					UI.Width,
					Layout.FooterHeight
				),
				0.045f,
				Palette.BorderSubtle
			);
		}


		// =========================================================================
		// UTILITIES
		// =========================================================================

		static string ResolutionToString(
			Vector2Int r)
		{
			return $"{r.x} x {r.y}";
		}


		static void Quit()
		{
			Application.Quit();
		}


		// =========================================================================
		// ENUMS
		// =========================================================================

		enum MenuScreen
		{
			Main,
			LoadProject,
			Settings,
			About,
			ThemeEditor
		}


		enum PopupKind
		{
			None,
			DeleteConfirmation,
			NamePopup_RenameProject,
			NamePopup_DuplicateProject,
			NamePopup_NewProject
		}
	}
}
