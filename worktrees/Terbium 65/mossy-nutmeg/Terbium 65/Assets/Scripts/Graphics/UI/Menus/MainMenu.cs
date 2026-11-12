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
	// Layout constants - consistent spacing system
	static class Layout
	{
		public const float HeaderHeight = 4.0f;     // Top toolbar with breathing room
		public const float FooterHeight = 2.0f;     // Status footer
		public const float SidebarWidth = 15.0f;    // Fixed left navigation pane width
		public const float ContentMarginX = 3.0f;   // Horizontal margin between sidebar and workspace
		public const float ContentMarginY = 2.8f;   // Vertical margin from header to workspace
		public const float SectionSpacing = 2.8f;   // Spacing between major content sections
		public const float ElementSpacing = 1.4f;   // Spacing between related elements
		public const float CardHeight = 5.0f;       // Primary action card height
		public const float CardSpacing = 1.6f;      // Spacing between action cards
		public const float ProjectRowHeight = 2.5f; // Recent project row height
		public const float ProjectRowSpacing = 0.4f; // Spacing between recent project rows
		public const float NavButtonHeight = 2.2f;  // Sidebar navigation button height
		public const float NavButtonSpacing = 0.4f; // Spacing between sidebar buttons
	}

	public static class MainMenu
	{
		public const int MaxProjectNameLength = 20;
		const bool capitalize = true;

		static MenuScreen activeMenuScreen = MenuScreen.Main;
		static PopupKind activePopup = PopupKind.None;
		static AppSettings EditedAppSettings;

		static readonly UIHandle ID_ProjectNameInput = new("MainMenu_ProjectNameInputField");
		static readonly UIHandle ID_DisplayResolutionWheel = new("MainMenu_DisplayResolutionWheel");
		static readonly UIHandle ID_FullscreenWheel = new("MainMenu_FullscreenWheel");
		static readonly UIHandle ID_ProjectsScrollView = new("MainMenu_ProjectsScrollView");

		static readonly string[] SettingsWheelFullScreenOptions = { "OFF", "MAXIMIZED", "BORDERLESS", "EXCLUSIVE" };
		static readonly FullScreenMode[] FullScreenModes = { FullScreenMode.Windowed, FullScreenMode.MaximizedWindow, FullScreenMode.FullScreenWindow, FullScreenMode.ExclusiveFullScreen };
		static readonly string[] SettingsWheelVSyncOptions = { "DISABLED", "ENABLED" };

		static readonly Func<string, bool> projectNameValidator = ProjectNameValidator;
		static readonly UI.ScrollViewDrawContentFunc loadProjectScrollViewDrawer = DrawAllProjectsInScrollView;

		// Sidebar navigation buttons
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

		static readonly string[] ResolutionNames = Resolutions.Select(r => ResolutionToString(r)).ToArray();
		static readonly string[] FullScreenResName = Resolutions.Select(r => ResolutionToString(Main.FullScreenResolution)).ToArray();
		static readonly string[] settingsButtonGroupNames = { "EXIT", "APPLY" };
		static readonly bool[] settingsButtonGroupStates = new bool[settingsButtonGroupNames.Length];

		static readonly bool[] openProjectButtonStates = new bool[openProjectButtonNames.Length];

		static ProjectDescription[] allProjectDescriptions;
		static string[] allProjectNames;
		static (bool compatible, string message)[] projectCompatibilities;

		static int selectedProjectIndex;

		static readonly string authorString = "Terbium 65 • Ternary Logic Design Environment";
		static readonly string versionString = "v0.1.0";
		static string SelectedProjectName => allProjectDescriptions[selectedProjectIndex].ProjectName;

		static string FormatButtonString(string s) => capitalize ? s.ToUpper() : s;

		// Material Dark Flat White palette
		static class Palette
		{
			public static readonly Color Background = ColHelper.MakeCol("#121212");
			public static readonly Color Surface = ColHelper.MakeCol("#1E1E1E");
			public static readonly Color SurfaceElevated = ColHelper.MakeCol("#2C2C2C");
			public static readonly Color Border = ColHelper.MakeCol("#333333");
			public static readonly Color TextPrimary = ColHelper.MakeCol("#FFFFFF");
			public static readonly Color TextSecondary = ColHelper.MakeCol("#A0A0A0");
			public static readonly Color TextDisabled = ColHelper.MakeCol("#666666");
			public static readonly Color Accent = ColHelper.MakeCol("#FFFFFF");
		}

		static ButtonTheme GetNavButtonTheme(DrawSettings.UIThemeDLS theme, bool isSelected = false) => new()
		{
			font = theme.FontRegular,
			fontSize = theme.FontSizeRegular * 0.9f,
			textCols = new ButtonTheme.StateCols(isSelected ? Palette.TextPrimary : Palette.TextSecondary, Palette.TextPrimary, Palette.TextPrimary, Palette.TextDisabled),
			buttonCols = new ButtonTheme.StateCols(isSelected ? Palette.SurfaceElevated : Color.clear, Palette.SurfaceElevated, Palette.Border, Color.clear),
			paddingScale = Vector2.zero
		};

		public static void Draw()
		{
			Simulator.UpdateInPausedState();
			
			if (KeyboardShortcuts.CancelShortcutTriggered && activePopup == PopupKind.None && activeMenuScreen != MenuScreen.Main)
			{
				BackToMain();
			}

			// Main application background (#101112)
			UI.DrawFullscreenPanel(Palette.Background);

			DrawHeader();
			DrawFooter();

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
						activeMenuScreen = MenuScreen.Settings;
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
			activeMenuScreen = MenuScreen.Main;
			activePopup = PopupKind.None;
			selectedProjectIndex = -1;
		}

		static void DrawMainScreen()
		{
			if (activePopup != PopupKind.None) return;

			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;
			RefreshLoadedProjects();

			// Draw docked sidebar
			DrawSidebar(theme);

			// Draw main workspace
			DrawMainWorkspace(theme);
		}

		static void DrawSidebar(DrawSettings.UIThemeDLS theme)
		{
			float sidebarHeight = UI.Height - Layout.HeaderHeight - Layout.FooterHeight;

			// Sidebar background pane (#18191A)
			UI.DrawPanel(new Vector2(0, Layout.FooterHeight),
				new Vector2(Layout.SidebarWidth, sidebarHeight),
				Palette.Surface, Anchor.BottomLeft);

			// Vertical separator line (#2B2C2D)
			UI.DrawLine(new Vector2(Layout.SidebarWidth, Layout.FooterHeight),
				new Vector2(Layout.SidebarWidth, UI.Height - Layout.HeaderHeight),
				0.08f, Palette.Border);

			float navWidth = Layout.SidebarWidth - 2.4f;
			float navX = 1.2f;
			float currentY = UI.Height - Layout.HeaderHeight - 2.0f;

			// PROJECT section label
			UI.DrawText("PROJECT", theme.FontRegular, theme.FontSizeRegular * 0.68f,
				new Vector2(1.8f, currentY), Anchor.TopLeft,
				Palette.TextDisabled);

			currentY -= 1.4f;

			// New Project nav button
			ButtonTheme newBtnTheme = GetNavButtonTheme(theme, true);
			bool newClicked = UI.Button("New Project", newBtnTheme,
				new Vector2(navX, currentY),
				new Vector2(navWidth, Layout.NavButtonHeight),
				true, false, false, Anchor.TopLeft, true, 1.0f);

			if (newClicked || KeyboardShortcuts.MainMenu_NewProjectShortcutTriggered)
			{
				activePopup = PopupKind.NamePopup_NewProject;
			}

			currentY -= Layout.NavButtonHeight + Layout.NavButtonSpacing;

			// Open Project nav button
			ButtonTheme openBtnTheme = GetNavButtonTheme(theme, false);
			bool openClicked = UI.Button("Open Project", openBtnTheme,
				new Vector2(navX, currentY),
				new Vector2(navWidth, Layout.NavButtonHeight),
				true, false, false, Anchor.TopLeft, true, 1.0f);
			if (openClicked || KeyboardShortcuts.MainMenu_OpenProjectShortcutTriggered)
			{
				selectedProjectIndex = -1;
				activeMenuScreen = MenuScreen.LoadProject;
			}

			currentY -= Layout.NavButtonHeight + 1.6f;

			// Horizontal divider line
			UI.DrawLine(new Vector2(1.8f, currentY), new Vector2(Layout.SidebarWidth - 1.8f, currentY), 0.05f, Palette.Border);

			currentY -= 1.6f;

			// APPLICATION section label
			UI.DrawText("APPLICATION", theme.FontRegular, theme.FontSizeRegular * 0.68f,
				new Vector2(1.8f, currentY), Anchor.TopLeft,
				Palette.TextDisabled);

			currentY -= 1.4f;

			// Settings button
			ButtonTheme settingsBtnTheme = GetNavButtonTheme(theme, false);
			bool settingsClicked = UI.Button("Settings", settingsBtnTheme,
				new Vector2(navX, currentY),
				new Vector2(navWidth, Layout.NavButtonHeight),
				true, false, false, Anchor.TopLeft, true, 1.0f);
			if (settingsClicked || KeyboardShortcuts.MainMenu_SettingsShortcutTriggered)
			{
				EditedAppSettings = Main.ActiveAppSettings;
				activeMenuScreen = MenuScreen.Settings;
				OnSettingsMenuOpened();
			}

			currentY -= Layout.NavButtonHeight + Layout.NavButtonSpacing;

			// About button
			ButtonTheme aboutBtnTheme = GetNavButtonTheme(theme, false);
			bool aboutClicked = UI.Button("About", aboutBtnTheme,
				new Vector2(navX, currentY),
				new Vector2(navWidth, Layout.NavButtonHeight),
				true, false, false, Anchor.TopLeft, true, 1.0f);
			if (aboutClicked)
			{
				activeMenuScreen = MenuScreen.About;
			}

			// Divider above Quit button
			float quitDividerY = Layout.FooterHeight + 1.8f + Layout.NavButtonHeight;
			UI.DrawLine(new Vector2(1.8f, quitDividerY), new Vector2(Layout.SidebarWidth - 1.8f, quitDividerY), 0.05f, Palette.Border);

			// Quit button at bottom of sidebar
			float quitY = Layout.FooterHeight + 1.0f + Layout.NavButtonHeight;
			ButtonTheme quitBtnTheme = GetNavButtonTheme(theme, false);
			bool quitClicked = UI.Button("Quit", quitBtnTheme,
				new Vector2(navX, quitY),
				new Vector2(navWidth, Layout.NavButtonHeight),
				true, false, false, Anchor.TopLeft, true, 1.0f);
			if (quitClicked || KeyboardShortcuts.MainMenu_QuitShortcutTriggered)
			{
				Quit();
			}
		}

		static void DrawMainWorkspace(DrawSettings.UIThemeDLS theme)
		{
			float workspaceLeft = Layout.SidebarWidth + Layout.ContentMarginX;
			float workspaceRight = UI.Width - Layout.ContentMarginX;
			float workspaceTop = UI.Height - Layout.HeaderHeight - Layout.ContentMarginY;
			float workspaceWidth = workspaceRight - workspaceLeft;

			Vector2 contentPos = new(workspaceLeft, workspaceTop);

			// Welcome heading
			UI.DrawText("Welcome to Terbium 65", theme.FontBold, theme.FontSizeRegular * 1.25f,
				contentPos, Anchor.TopLeft, Palette.TextPrimary);

			// Subtitle description (restore breathing room)
			contentPos.y -= 1.8f;
			UI.DrawText("Design and simulate ternary logic circuits.", theme.FontRegular, theme.FontSizeRegular * 0.88f,
				contentPos, Anchor.TopLeft, Palette.TextSecondary);

			// Section: QUICK START
			contentPos.y -= 3.0f;
			UI.DrawText("QUICK START", theme.FontRegular, theme.FontSizeRegular * 0.68f,
				contentPos, Anchor.TopLeft, Palette.TextDisabled);

			contentPos.y -= 1.2f;

			// Two-column layout for action cards with a maximum width so they don't stretch infinitely
			float maxContentWidth = 55.0f;
			float effectiveWidth = Mathf.Min(workspaceWidth, maxContentWidth);
			float cardWidth = (effectiveWidth - Layout.CardSpacing) / 2f;
			float cardLeft = workspaceLeft;
			float cardRight = cardLeft + cardWidth + Layout.CardSpacing;

			// New Project card
			bool newCardClicked = DrawActionCard(theme, new Vector2(cardLeft, contentPos.y), 
				new Vector2(cardWidth, Layout.CardHeight),
				"New Project", "Create a new ternary circuit design.");
			if (newCardClicked)
			{
				activePopup = PopupKind.NamePopup_NewProject;
			}

			// Open Project card
			bool openCardClicked = DrawActionCard(theme, new Vector2(cardRight, contentPos.y),
				new Vector2(cardWidth, Layout.CardHeight),
				"Open Project", "Open an existing project.");
			if (openCardClicked)
			{
				selectedProjectIndex = -1;
				activeMenuScreen = MenuScreen.LoadProject;
			}

			// Section: RECENT PROJECTS
			contentPos.y -= Layout.CardHeight + 2.2f;
			UI.DrawText("RECENT PROJECTS", theme.FontRegular, theme.FontSizeRegular * 0.68f,
				contentPos, Anchor.TopLeft, Palette.TextDisabled);

			contentPos.y -= 1.0f;

			if (allProjectDescriptions == null || allProjectDescriptions.Length == 0)
			{
				UI.DrawText("No recent projects.", theme.FontRegular, theme.FontSizeRegular * 0.88f,
					contentPos, Anchor.TopLeft, Palette.TextDisabled);
			}
			else
			{
				float rowY = contentPos.y;
				float minBottom = Layout.FooterHeight + 1.2f;
				int maxVisibleRows = Mathf.Max(1, Mathf.FloorToInt((rowY - minBottom) / (Layout.ProjectRowHeight + Layout.ProjectRowSpacing)));
				int count = Mathf.Min(allProjectDescriptions.Length, maxVisibleRows);

				for (int i = 0; i < count; i++)
				{
					ProjectDescription desc = allProjectDescriptions[i];
					Vector2 rowPos = new(workspaceLeft, rowY);
					Vector2 rowSize = new(effectiveWidth, Layout.ProjectRowHeight);

					bool rowClicked = DrawProjectRow(theme, rowPos, rowSize, desc.ProjectName);
					if (rowClicked)
					{
						Main.CreateOrLoadProject(desc.ProjectName, string.Empty);
					}

					rowY -= Layout.ProjectRowHeight + Layout.ProjectRowSpacing;
				}
			}
		}

		static bool DrawActionCard(DrawSettings.UIThemeDLS theme, Vector2 pos, Vector2 size, string title, string description)
		{
			ButtonTheme cardBtnTheme = new()
			{
				font = theme.FontRegular,
				fontSize = theme.FontSizeRegular,
				textCols = new ButtonTheme.StateCols(Color.clear, Color.clear, Color.clear, Color.clear),
				buttonCols = new ButtonTheme.StateCols(Palette.Surface, Palette.SurfaceElevated, Palette.SurfaceElevated, Palette.Surface),
				paddingScale = Vector2.zero
			};

			Bounds2D cardBounds = Bounds2D.CreateFromTopLeftAndSize(pos, size);
			bool mouseOver = UI.MouseInsideBounds(cardBounds);

			Color bgCol = mouseOver ? Palette.SurfaceElevated : Palette.Surface;
			Color borderCol = mouseOver ? Palette.Accent : Palette.Border;

			// Card background panel
			UI.DrawPanel(pos, size, bgCol, Anchor.TopLeft);

			// Bottom border only (minimal flat style)
			Vector2 bottomLeft = pos + new Vector2(0, -size.y);
			Vector2 bottomRight = pos + new Vector2(size.x, -size.y);
			UI.DrawLine(bottomLeft, bottomRight, 0.06f, borderCol);

			// Title
			Vector2 titlePos = pos + new Vector2(1.2f, -1.2f);
			UI.DrawText(title, theme.FontBold, theme.FontSizeRegular * 0.95f,
				titlePos, Anchor.TopLeft, mouseOver ? Palette.TextPrimary : Palette.TextPrimary);

			// Description
			Vector2 descPos = pos + new Vector2(1.2f, -2.8f);
			UI.DrawText(description, theme.FontRegular, theme.FontSizeRegular * 0.78f,
				descPos, Anchor.TopLeft, Palette.TextSecondary);

			// Click handler
			return UI.Button("", cardBtnTheme, pos, size, true, false, false, Anchor.TopLeft);
		}

		static bool DrawProjectRow(DrawSettings.UIThemeDLS theme, Vector2 pos, Vector2 size, string projectName)
		{
			ButtonTheme rowBtnTheme = new()
			{
				font = theme.FontRegular,
				fontSize = theme.FontSizeRegular,
				textCols = new ButtonTheme.StateCols(Color.clear, Color.clear, Color.clear, Color.clear),
				buttonCols = new ButtonTheme.StateCols(Color.clear, Palette.SurfaceElevated, Palette.SurfaceElevated, Color.clear),
				paddingScale = Vector2.zero
			};

			Bounds2D rowBounds = Bounds2D.CreateFromTopLeftAndSize(pos, size);
			bool mouseOver = UI.MouseInsideBounds(rowBounds);

			// Subtle hover background only
			if (mouseOver)
			{
				UI.DrawPanel(pos, size, Palette.SurfaceElevated, Anchor.TopLeft);
			}

			// Bottom divider line only (minimal)
			Vector2 bottomLeft = pos + new Vector2(0, -size.y);
			Vector2 bottomRight = pos + new Vector2(size.x, -size.y);
			UI.DrawLine(bottomLeft, bottomRight, 0.04f, Palette.Border);

			// Project name
			Vector2 namePos = pos + new Vector2(1.2f, -size.y / 2f);
			UI.DrawText(projectName, theme.FontRegular, theme.FontSizeRegular * 0.9f,
				namePos, Anchor.CentreLeft, mouseOver ? Palette.TextPrimary : Palette.TextSecondary);

			return UI.Button("", rowBtnTheme, pos, size, true, false, false, Anchor.TopLeft);
		}

		static void DrawLoadProjectScreen()
		{
			const int backButtonIndex = 0;
			const int deleteButtonIndex = 1;
			const int duplicateButtonIndex = 2;
			const int renameButtonIndex = 3;
			const int openButtonIndex = 4;
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;
			RefreshLoadedProjects();

			// Draw sidebar with back button
			DrawSidebarWithBack(theme);

			// Main workspace
			float workspaceLeft = Layout.SidebarWidth + Layout.ContentMarginX;
			float workspaceRight = UI.Width - Layout.ContentMarginX;
			float workspaceTop = UI.Height - Layout.HeaderHeight - Layout.ContentMarginY;
			float workspaceWidth = workspaceRight - workspaceLeft;

			Vector2 contentPos = new(workspaceLeft, workspaceTop);

			// Title
			UI.DrawText("Open Project", theme.FontBold, theme.FontSizeRegular * 1.15f,
				contentPos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));

			// Projects list
			contentPos.y -= 2.0f;
			Vector2 projectsScrollSize = new(workspaceWidth, 14f);
			UI.DrawScrollView(ID_ProjectsScrollView, contentPos, projectsScrollSize,
				Anchor.TopLeft, theme.ScrollTheme, loadProjectScrollViewDrawer);

			ButtonTheme buttonTheme = theme.MainMenuButtonTheme;

			bool projectSelected = selectedProjectIndex >= 0 && selectedProjectIndex < allProjectDescriptions.Length;
			bool compatibleProject = projectSelected && projectCompatibilities[selectedProjectIndex].compatible;

			for (int i = 0; i < openProjectButtonStates.Length; i++)
			{
				bool buttonEnabled = activePopup == PopupKind.None && (compatibleProject || i == backButtonIndex || (i == deleteButtonIndex && projectSelected));
				openProjectButtonStates[i] = buttonEnabled;
			}

			Vector2 buttonRegionPos = UI.PrevBounds.BottomLeft + Vector2.down * 1f;
			int buttonIndex = UI.HorizontalButtonGroup(openProjectButtonNames, openProjectButtonStates, buttonTheme,
				buttonRegionPos, UI.PrevBounds.Width, UILayoutHelper.DefaultSpacing, 0, Anchor.TopLeft);

			if (projectSelected && !compatibleProject)
			{
				Vector2 errorMessagePos = UI.PrevBounds.BottomLeft + Vector2.down * 0.7f;
				UI.DrawText(projectCompatibilities[selectedProjectIndex].message, buttonTheme.font, buttonTheme.fontSize * 0.8f,
					errorMessagePos, Anchor.TopLeft, new Color(1, 0.8f, 0.2f, 0.8f));
			}

			// Handle button input
			if (buttonIndex == backButtonIndex) BackToMain();
			else if (buttonIndex == deleteButtonIndex) activePopup = PopupKind.DeleteConfirmation;
			else if (buttonIndex == duplicateButtonIndex) activePopup = PopupKind.NamePopup_DuplicateProject;
			else if (buttonIndex == renameButtonIndex) activePopup = PopupKind.NamePopup_RenameProject;
			else if (buttonIndex == openButtonIndex) Main.CreateOrLoadProject(SelectedProjectName, string.Empty);
		}

		static void DrawSidebarWithBack(DrawSettings.UIThemeDLS theme)
		{
			float sidebarHeight = UI.Height - Layout.HeaderHeight - Layout.FooterHeight;

			// Full docked sidebar
			UI.DrawPanel(new Vector2(0, Layout.FooterHeight),
				new Vector2(Layout.SidebarWidth, sidebarHeight),
				ColHelper.MakeCol("#17191C"), Anchor.BottomLeft);

			// Right Divider
			UI.DrawLine(new Vector2(Layout.SidebarWidth, Layout.FooterHeight),
				new Vector2(Layout.SidebarWidth, UI.Height - Layout.HeaderHeight),
				0.08f, ColHelper.MakeCol("#292D32"));

			ButtonTheme navTheme = GetNavButtonTheme(theme);
			float currentY = UI.Height - Layout.HeaderHeight - 1.8f;
			float navWidth = Layout.SidebarWidth - 1.6f;
			float navX = 0.8f;

			bool backClicked = UI.Button("← Back", navTheme,
				new Vector2(navX, currentY),
				new Vector2(navWidth, Layout.NavButtonHeight),
				true, false, false, Anchor.TopLeft, true, 0.8f);
			if (backClicked)
			{
				BackToMain();
			}
		}

		static bool ProjectNameValidator(string inputString) => inputString.Length <= 20 && !SaveUtils.NameContainsForbiddenChar(inputString);

		static void DrawAllProjectsInScrollView(Vector2 topLeft, float width, bool isLayoutPass)
		{
			float spacing = 0.3f;
			bool enabled = activePopup == PopupKind.None;

			for (int i = 0; i < allProjectDescriptions.Length; i++)
			{
				ProjectDescription desc = allProjectDescriptions[i];
				bool selected = i == selectedProjectIndex;
				ButtonTheme buttonTheme = selected ? DrawSettings.ActiveUITheme.ProjectSelectionButtonSelected : DrawSettings.ActiveUITheme.ProjectSelectionButton;
				if (!projectCompatibilities[i].compatible) buttonTheme.textCols.normal.a = 0.5f;

				if (UI.Button(desc.ProjectName, buttonTheme, topLeft, new Vector2(width, Layout.ProjectRowHeight), enabled, false, false, Anchor.TopLeft, true, 0.8f))
				{
					selectedProjectIndex = i;
				}

				topLeft = UI.PrevBounds.BottomLeft + Vector2.down * spacing;
			}
		}

		static void RefreshLoadedProjects()
		{
			allProjectDescriptions = Loader.LoadAllProjectDescriptions();
			allProjectNames = allProjectDescriptions.Select(d => d.ProjectName).ToArray();
			projectCompatibilities = allProjectDescriptions.Select(d => CanOpenProject(d)).ToArray();
		}

		static (bool canOpen, string failureReason) CanOpenProject(ProjectDescription projectDescription)
		{
			try
			{
				Main.Version earliestCompatible = Main.Version.Parse(projectDescription.DLSVersion_EarliestCompatible);
				Main.Version currentVersion = Main.DLSVersion;

				// In case project was made with a newer version of the sim, check if this version is able to open it
				bool canOpen = currentVersion.ToInt() >= earliestCompatible.ToInt();
				string failureReason = canOpen ? string.Empty : $"This project requires version {earliestCompatible} or later.";
				return (canOpen, failureReason);
			}
			catch
			{
				Debug.Log("Incompatible project: " + projectDescription.ProjectName);
				return (false, "Unrecognized project format");
			}
		}

		static void BackToMain()
		{
			UI.GetInputFieldState(ID_ProjectNameInput).ClearText();
			activeMenuScreen = MenuScreen.Main;
			activePopup = PopupKind.None;
		}

		static void OnSettingsMenuOpened()
		{
			// Automatically select whichever resolution option is closest to current window size
			WheelSelectorState resolutionWheelState = UI.GetWheelSelectorState(ID_DisplayResolutionWheel);
			int closestMatchError = int.MaxValue;
			for (int i = 0; i < Resolutions.Length; i++)
			{
				int matchError = Mathf.Min(Mathf.Abs(Screen.width - Resolutions[i].x), Mathf.Abs(Screen.height - Resolutions[i].y));
				if (matchError < closestMatchError)
				{
					closestMatchError = matchError;
					resolutionWheelState.index = i;
				}
			}

			// Automatically set curr fullscreen mode
			WheelSelectorState fullscreenWheelState = UI.GetWheelSelectorState(ID_FullscreenWheel);
			for (int i = 0; i < FullScreenModes.Length; i++)
			{
				if (Screen.fullScreenMode == FullScreenModes[i])
				{
					fullscreenWheelState.index = i;
					break;
				}
			}
		}

		static void DrawSettingsScreen()
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;

			// Draw sidebar with back button
			DrawSidebarWithBack(theme);

			// Main workspace
			float workspaceLeft = Layout.SidebarWidth + Layout.ContentMarginX;
			float workspaceRight = UI.Width - Layout.ContentMarginX;
			float workspaceTop = UI.Height - Layout.HeaderHeight - Layout.ContentMarginY;

			Vector2 contentPos = new(workspaceLeft, workspaceTop);

			// Title
			UI.DrawText("Settings", theme.FontBold, theme.FontSizeRegular * 1.15f,
				contentPos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));

			contentPos.y -= 2.6f;

			using (UI.BeginBoundsScope(true))
			{
				Draw.ID panelID = UI.ReservePanel();

				float controlRight = workspaceRight - 0.5f;
				Vector2 wheelSize = new(12f, 2.1f);
				Vector2 pos = contentPos;

				// Resolution
				bool resEnabled = EditedAppSettings.fullscreenMode == FullScreenMode.Windowed;
				UI.DrawText("Resolution", theme.FontRegular, theme.FontSizeRegular * 0.9f, pos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));
				string[] resNames = resEnabled ? ResolutionNames : FullScreenResName;
				int resIndex = UI.WheelSelector(ID_DisplayResolutionWheel, resNames, 
					new Vector2(controlRight, pos.y + 1f), wheelSize, theme.OptionsWheel, Anchor.CentreRight, enabled: resEnabled);
				EditedAppSettings.ResolutionX = Resolutions[resIndex].x;
				EditedAppSettings.ResolutionY = Resolutions[resIndex].y;

				// Fullscreen
				pos += Vector2.down * 3.2f;
				UI.DrawText("Fullscreen", theme.FontRegular, theme.FontSizeRegular * 0.9f, pos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));
				int fullScreenSettingIndex = UI.WheelSelector(ID_FullscreenWheel, SettingsWheelFullScreenOptions,
					new Vector2(controlRight, pos.y + 1f), wheelSize, theme.OptionsWheel, Anchor.CentreRight);
				EditedAppSettings.fullscreenMode = FullScreenModes[fullScreenSettingIndex];

				// VSync
				pos += Vector2.down * 3.2f;
				UI.DrawText("VSync", theme.FontRegular, theme.FontSizeRegular * 0.9f, pos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));
				int vsyncSetting = UI.WheelSelector(EditedAppSettings.VSyncEnabled ? 1 : 0, SettingsWheelVSyncOptions,
					new Vector2(controlRight, pos.y + 1f), wheelSize, theme.OptionsWheel, Anchor.CentreRight);
				EditedAppSettings.VSyncEnabled = vsyncSetting == 1;

				// Theme
				pos += Vector2.down * 3.2f;
				UI.DrawText("Theme", theme.FontRegular, theme.FontSizeRegular * 0.9f, pos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));
				bool editThemeClicked = UI.Button("EDIT THEME", theme.MenuButtonTheme,
					new Vector2(controlRight - 6.5f, pos.y + 1f), new Vector2(13f, 2f),
					true, false, true, Anchor.Centre);
				if (editThemeClicked)
				{
					ThemeEditorMenu.OnMenuOpened();
					activeMenuScreen = MenuScreen.ThemeEditor;
				}

				// Background panel
				UI.ModifyPanel(panelID, UI.GetCurrentBoundsScope().Centre, UI.GetCurrentBoundsScope().Size + Vector2.one * 1.5f, 
					ColHelper.MakeCol("#1D2024"));
			}

			Vector2 buttonPos = UI.PrevBounds.BottomLeft + Vector2.down * 1.2f;
			settingsButtonGroupStates[0] = true;
			settingsButtonGroupStates[1] = true;

			int buttonIndex = UI.HorizontalButtonGroup(settingsButtonGroupNames, settingsButtonGroupStates,
				theme.MainMenuButtonTheme, buttonPos, UI.PrevBounds.Width, UILayoutHelper.DefaultSpacing, 0, Anchor.TopLeft);

			if (buttonIndex == 0)
			{
				BackToMain();
			}
			else if (buttonIndex == 1)
			{
				Main.SaveAndApplyAppSettings(EditedAppSettings);
			}
		}

		static void DrawNamePopup()
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;

			UI.StartNewLayer();
			UI.DrawFullscreenPanel(theme.MenuBackgroundOverlayCol);

			using (UI.BeginBoundsScope(true))
			{
				Draw.ID panelID = UI.ReservePanel();

				InputFieldTheme inputTheme = theme.ChipNameInputField;

				Vector2 charSize = UI.CalculateTextSize("M", inputTheme.fontSize, inputTheme.font);
				Vector2 padding = new(2, 2);
				Vector2 inputFieldSize = new Vector2(charSize.x * MaxProjectNameLength, charSize.y) + padding * 2;

				InputFieldState state = UI.InputField(ID_ProjectNameInput, inputTheme, UI.Centre, inputFieldSize, "", Anchor.Centre, padding.x, projectNameValidator, true);

				string projectName = state.text;
				bool validProjectName = !string.IsNullOrWhiteSpace(projectName) && SaveUtils.ValidFileName(projectName);
				bool projectNameAlreadyExists = false;
				foreach (string existingProjectName in allProjectNames)
				{
					projectNameAlreadyExists |= string.Equals(projectName, existingProjectName, StringComparison.CurrentCultureIgnoreCase);
				}

				bool canCreateProject = validProjectName && !projectNameAlreadyExists;

				Vector2 buttonsRegionSize = new(inputFieldSize.x, 5);
				Vector2 buttonsRegionCentre = UILayoutHelper.CalculateCentre(UI.PrevBounds.BottomLeft, buttonsRegionSize, Anchor.TopLeft);
				(Vector2 size, Vector2 centre) layoutCancel = UILayoutHelper.HorizontalLayout(2, 0, buttonsRegionCentre, buttonsRegionSize);
				(Vector2 size, Vector2 centre) layoutConfirm = UILayoutHelper.HorizontalLayout(2, 1, buttonsRegionCentre, buttonsRegionSize);

				bool cancelButton = UI.Button("CANCEL", theme.MainMenuButtonTheme, layoutCancel.centre, new Vector2(layoutCancel.size.x, 0), true, false, true);
				bool confirmButton = UI.Button("CONFIRM", theme.MainMenuButtonTheme, layoutConfirm.centre, new Vector2(layoutConfirm.size.x, 0), canCreateProject, false, true);

				if (cancelButton || KeyboardShortcuts.CancelShortcutTriggered)
				{
					state.ClearText();
					activePopup = PopupKind.None;
				}

				if (confirmButton || KeyboardShortcuts.ConfirmShortcutTriggered)
				{
					state.ClearText();
					PopupKind kind = activePopup;
					activePopup = PopupKind.None;
					OnNamePopupConfirmed(kind, projectName);
				}

				UI.ModifyPanel(panelID, UI.GetCurrentBoundsScope().Centre, UI.GetCurrentBoundsScope().Size + Vector2.one * 2, theme.MenuPanelCol);
			}
		}

		static void OnNamePopupConfirmed(PopupKind kind, string name)
		{
			if (kind is PopupKind.NamePopup_RenameProject or PopupKind.NamePopup_DuplicateProject)
			{
				if (kind is PopupKind.NamePopup_RenameProject) Saver.RenameProject(SelectedProjectName, name);
				if (kind is PopupKind.NamePopup_DuplicateProject) Saver.DuplicateProject(SelectedProjectName, name);

				RefreshLoadedProjects();
				selectedProjectIndex = 0; // the modified project will now be at top of list
				UI.GetScrollbarState(ID_ProjectsScrollView).scrollY = 0; // scroll to top so selection is visible
			}
			else if (kind is PopupKind.NamePopup_NewProject)
			{
				Main.CreateOrLoadProject(name);
			}
		}

		static void DrawDeleteProjectConfirmationPopup()
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;

			UI.StartNewLayer();
			UI.DrawFullscreenPanel(theme.MenuBackgroundOverlayCol);

			using (UI.BeginBoundsScope(true))
			{
				Draw.ID panelID = UI.ReservePanel();
				UI.DrawText("Are you sure you want to delete this project?", theme.FontRegular, theme.FontSizeRegular, UI.Centre, Anchor.Centre, Color.yellow);

				Vector2 buttonRegionTopLeft = UI.PrevBounds.BottomLeft + Vector2.down * DrawSettings.VerticalButtonSpacing;
				float buttonRegionWidth = UI.PrevBounds.Width;
				int buttonIndex = UI.HorizontalButtonGroup(new[] { "CANCEL", "DELETE" }, theme.MainMenuButtonTheme, buttonRegionTopLeft, buttonRegionWidth, DrawSettings.HorizontalButtonSpacing, 0, Anchor.TopLeft);
				UI.ModifyPanel(panelID, UI.GetCurrentBoundsScope().Centre, UI.GetCurrentBoundsScope().Size + Vector2.one * 2, theme.MenuPanelCol);

				if (buttonIndex == 0) // Cancel
				{
					activePopup = PopupKind.None;
				}
				else if (buttonIndex == 1) // Delete
				{
					Saver.DeleteProject(SelectedProjectName);
					selectedProjectIndex = -1;
					RefreshLoadedProjects();
					activePopup = PopupKind.None;
				}
			}
		}

		static void DrawAboutScreen()
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;

			// Draw sidebar with back button
			DrawSidebarWithBack(theme);

			// Main workspace
			float workspaceLeft = Layout.SidebarWidth + Layout.ContentMarginX;
			float workspaceTop = UI.Height - Layout.HeaderHeight - Layout.ContentMarginY;

			Vector2 contentPos = new(workspaceLeft, workspaceTop);

			// Title
			UI.DrawText("About", theme.FontBold, theme.FontSizeRegular * 1.15f,
				contentPos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));

			// About text
			contentPos += Vector2.down * 2.4f;
			string aboutText = "Terbium 65 is a digital logic simulation\n" +
				"environment for designing and experimenting\n" +
				"with ternary circuits and ternary computer\n" +
				"architectures.\n\n" +
				"Originally created by Sebastian Lague\n" +
				"as Digital Logic Sim.\n\n" +
				"Forked and modified by DevaHarsha28.";

			UI.DrawText(aboutText, theme.FontRegular, theme.FontSizeRegular * 0.9f,
				contentPos, Anchor.TopLeft, ColHelper.MakeCol("#E2E5E8"));
		}

		static void DrawHeader()
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;

			// Header background (#18191A)
			UI.DrawPanel(new Vector2(0, UI.Height), 
				new Vector2(UI.Width, Layout.HeaderHeight),
				Palette.Surface, Anchor.TopLeft);

			// Bottom border (#2B2C2D)
			UI.DrawLine(new Vector2(0, UI.Height - Layout.HeaderHeight),
				new Vector2(UI.Width, UI.Height - Layout.HeaderHeight),
				0.08f, Palette.Border);

			// Left: Title with subtitle
			float titleLeft = 2.0f;
			float titleTop = UI.Height - 0.8f;
			UI.DrawText("TERBIUM 65", theme.FontBold, theme.FontSizeRegular * 1.0f,
				new Vector2(titleLeft, titleTop), Anchor.TopLeft, Palette.TextPrimary);

			float subtitleTop = UI.Height - 2.4f;
			UI.DrawText("Ternary Logic Design Environment", theme.FontRegular, theme.FontSizeRegular * 0.75f,
				new Vector2(titleLeft, subtitleTop), Anchor.TopLeft, Palette.TextSecondary);

			// Right: Version
			float titleRight = UI.Width - 2.0f;
			UI.DrawText(versionString, theme.FontRegular, theme.FontSizeRegular * 0.78f,
				new Vector2(titleRight, UI.Height - Layout.HeaderHeight / 2), Anchor.CentreRight, Palette.TextSecondary);
		}

		static void DrawFooter()
		{
			DrawSettings.UIThemeDLS theme = DrawSettings.ActiveUITheme;

			// Footer background (#18191A)
			UI.DrawPanel(new Vector2(0, 0), 
				new Vector2(UI.Width, Layout.FooterHeight),
				Palette.Surface, Anchor.BottomLeft);

			// Top border (#2B2C2D)
			UI.DrawLine(new Vector2(0, Layout.FooterHeight),
				new Vector2(UI.Width, Layout.FooterHeight),
				0.08f, Palette.Border);

			// Left: Author string
			float footerLeft = 2.0f;
			UI.DrawText(authorString, theme.FontRegular, theme.FontSizeRegular * 0.7f,
				new Vector2(footerLeft, Layout.FooterHeight / 2), Anchor.CentreLeft, 
				Palette.TextDisabled);

			// Right: Version tag
			float footerRight = UI.Width - 2.0f;
			UI.DrawText(versionString, theme.FontRegular, theme.FontSizeRegular * 0.7f,
				new Vector2(footerRight, Layout.FooterHeight / 2), Anchor.CentreRight,
				Palette.TextDisabled);
		}

		static string ResolutionToString(Vector2Int r) => $"{r.x} x {r.y}";

		static void Quit()
		{
			Application.Quit();
		}

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