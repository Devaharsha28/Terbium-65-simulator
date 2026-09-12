using System.Linq;
using DLS.Game;
using Seb.Vis;
using Seb.Vis.UI;
using UnityEngine;

namespace DLS.Graphics
{
	// Docked editor chrome. All actions delegate to the existing project tools.
	public static class EditorWorkspace
	{
		static readonly UIHandle BrowserScroll = new("Workspace_Browser");
		static bool panelsVisible = true;
		static DrawSettings.UIThemeDLS Theme => DrawSettings.ActiveUITheme;
		static Color TextColor => ThemePalette.Parse(ThemeManager.ActivePalette.TextPrimary);
		static Color Muted => ThemePalette.Parse(ThemeManager.ActivePalette.TextSecondary);
		static Color Edge => ThemePalette.Parse(ThemeManager.ActivePalette.Border);

		static void Text(string text, float x, float y, float size = 1.2f, bool bold = false)
		{
			UI.DrawText(text, bold ? Theme.FontBold : Theme.FontRegular, size,
				new Vector2(x, y), Anchor.TopLeft, bold ? TextColor : Muted);
		}

		static bool Button(string label, float x, float y, float width, bool enabled = true)
		{
			var theme = Theme.ButtonTheme;
			theme.fontSize = 1.2f;
			return UI.Button(label, theme, new Vector2(x, y), new Vector2(width, 2.6f),
				enabled, false, false, Anchor.TopLeft);
		}

		static void Panel(float x, float top, float width, float height, string title)
		{
			UI.DrawPanel(new Vector2(x, top), new Vector2(width, height), Theme.MenuPanelCol, Anchor.TopLeft);
			UI.DrawPanel(new Vector2(x, top), new Vector2(width, 2.8f), Theme.StarredBarCol, Anchor.TopLeft);
			Text(title, x + 0.8f, top - 0.65f, 1.25f, true);
			UI.DrawLine(new Vector2(x, top), new Vector2(x, top - height), 0.05f, Edge);
			UI.DrawLine(new Vector2(x + width, top), new Vector2(x + width, top - height), 0.05f, Edge);
		}

		public static void Draw(Project project)
		{
			float top = UI.Height;
			float leftWidth = panelsVisible ? 18f : 0;
			float rightWidth = panelsVisible ? 19f : 0;
			UI.DrawPanel(new Vector2(0, top), new Vector2(UI.Width, 7.5f), Theme.MenuPanelCol, Anchor.TopLeft);
			Text("Tb  /  Terbium 65", 1, top - 0.6f, 1.45f, true);
			string chip = string.IsNullOrWhiteSpace(project.ActiveDevChipName) ? "Untitled circuit" : project.ActiveDevChipName;
			Text(chip + (project.ActiveChipHasUnsavedChanges() ? " *" : ""), 20, top - 0.75f, 1.3f, true);
			float barY = top - 3.4f;
			if (Button("Projects", 0.8f, barY, 8)) BottomBarUI.ExitToMainMenu();
			if (Button("New chip", 9.4f, barY, 8, project.CanEditViewedChip)) BottomBarUI.CreateNewChip();
			if (Button("Save", 18, barY, 7, project.CanEditViewedChip)) UIDrawer.SetActiveMenu(UIDrawer.MenuType.ChipSave);
			if (Button("Find", 25.6f, barY, 7, project.CanEditViewedChip)) UIDrawer.SetActiveMenu(UIDrawer.MenuType.Search);
			if (Button("Library", 33.2f, barY, 8)) UIDrawer.SetActiveMenu(UIDrawer.MenuType.ChipLibrary);
			if (Button(project.simPaused ? "Run" : "Pause", 43, barY, 7)) project.description.Prefs_SimPaused = !project.simPaused;
			if (Button("Step", 50.6f, barY, 6, project.simPaused)) project.advanceSingleSimStep = true;
			if (Button("Preferences", 58, barY, 11)) UIDrawer.SetActiveMenu(UIDrawer.MenuType.Preferences);
			if (Button(panelsVisible ? "Hide panels" : "Show panels", 70, barY, 11)) panelsVisible = !panelsVisible;
			if (project.chipViewStack.Count > 1 && Button("Back", 82, barY, 7)) project.ReturnToPreviousViewedChip();

			float dockTop = top - 7.5f;
			float dockHeight = dockTop - BottomBarUI.barHeight - 2.8f;
			if (panelsVisible)
			{
				Panel(0, dockTop, leftWidth, dockHeight, "Chip browser");
				Text("Click a chip to place it", 0.8f, dockTop - 3.6f, 1.05f);
				UI.DrawScrollView(BrowserScroll, new Vector2(0.5f, dockTop - 5.8f),
					new Vector2(leftWidth - 1, dockHeight - 6.3f), 0.3f, Anchor.TopLeft,
					Theme.ScrollTheme, DrawChip, project.chipLibrary.allChips.Count);
				float right = UI.Width - rightWidth;
				Panel(right, dockTop, rightWidth, dockHeight, "Circuit details");
				float y = dockTop - 4;
				Text("CURRENT CIRCUIT", right + 1, y, 1.05f, true);
				y -= 2.4f;
				// Clip long user-defined names to their panel rather than adjacent UI.
				using (UI.CreateMaskScope(new Vector2(right + rightWidth / 2, y - 1.2f), new Vector2(rightWidth - 2, 2.4f)))
					Text(chip, right + 1, y, 1.4f, true);
				y -= 4;
				Text("Components     " + project.ViewedChip.GetSubchips().Count(), right + 1, y); y -= 2.6f;
				Text("Connections    " + project.ViewedChip.Wires.Count, right + 1, y); y -= 2.6f;
				Text("Selected       " + project.controller.SelectedElements.Count, right + 1, y); y -= 4;
				Text("SIMULATION", right + 1, y, 1.05f, true); y -= 2.6f;
				Text(project.simPaused ? "Paused" : "Running", right + 1, y); y -= 2.6f;
				Text(project.targetTicksPerSecond + " ticks / second", right + 1, y); y -= 4;
				if (Button("Edit preferences", right + 1, y, rightWidth - 2)) UIDrawer.SetActiveMenu(UIDrawer.MenuType.Preferences);
			}
			// Graph tab strip and compact status bar stay clear of the graph itself.
			UI.DrawPanel(new Vector2(leftWidth, dockTop), new Vector2(UI.Width - leftWidth - rightWidth, 2.8f), Theme.InfoBarCol, Anchor.TopLeft);
			Text("Circuit graph", leftWidth + 1, dockTop - 0.65f, 1.25f, true);
			UI.DrawPanel(new Vector2(0, BottomBarUI.barHeight + 2.8f), new Vector2(UI.Width, 2.8f), Theme.MenuPanelCol, Anchor.TopLeft);
			Text(project.simPaused ? "Paused  |  Space: step" : "Simulation running", 1, BottomBarUI.barHeight + 2.1f);
			Text(project.CanEditViewedChip ? "Edit mode" : "Read-only view", 35, BottomBarUI.barHeight + 2.1f);
			Text(project.ActiveChipHasUnsavedChanges() ? "Unsaved changes" : "No unsaved changes", UI.Width - 17, BottomBarUI.barHeight + 2.1f);
		}

		static void DrawChip(Vector2 pos, float width, int index, bool layoutOnly)
		{
			var project = Project.ActiveProject;
			var chip = project.chipLibrary.allChips[index];
			var button = Theme.ChipButton;
			button.fontSize = 1.15f;
			bool allowed = project.CanEditViewedChip && project.ViewedChip.CanAddSubchip(chip.Name);
			if (UI.Button(chip.Name, button, pos, new Vector2(width, 2.5f), allowed,
				false, false, Anchor.TopLeft, true, 0.5f, layoutOnly || UI.GetScrollbarState(BrowserScroll).isDragging))
				project.controller.StartPlacing(chip);
		}
	}
}
