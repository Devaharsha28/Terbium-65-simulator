using DLS.Game;
using Seb.Types;
using Seb.Vis;
using Seb.Vis.UI;
using UnityEngine;

namespace DLS.Graphics
{
	public static partial class MainMenu
	{
		// Home uses explicit text slots; text height is measured before advancing
		// the layout so proportional font metrics cannot overlap adjacent content.
		static void HomeText(string text, Vector2 pos, float size, Color color, bool bold = false)
		{
			UI.DrawText(text, bold ? FontType.OpenSansBold : FontType.OpenSansRegular,
				size, pos, Anchor.TopLeft, color);
		}

		static void HomeSurface(Vector2 pos, Vector2 size, Color color, float radius = 0.8f)
		{
			UI.DrawPanel(pos, size, color, Anchor.TopLeft);
			Color edge = Palette.Border;
			UI.DrawLine(pos, pos + Vector2.right * size.x, 0.04f, edge);
			UI.DrawLine(pos, pos + Vector2.down * size.y, 0.04f, edge);
			UI.DrawLine(pos + Vector2.down * size.y, pos + new Vector2(size.x, -size.y), 0.04f, edge);
			UI.DrawLine(pos + Vector2.right * size.x, pos + new Vector2(size.x, -size.y), 0.04f, edge);
		}

		static bool HomeButton(string text, Vector2 pos, Vector2 size, bool primary = false)
		{
			bool hover = UI.MouseInsideBounds(Bounds2D.CreateFromTopLeftAndSize(pos, size));
			Color fill = primary ? Palette.Accent : Palette.SurfaceElevated;
			if (hover) fill = Color.Lerp(fill, Palette.TextPrimary, 0.10f);
			HomeSurface(pos, size, fill, 0.65f);
			var button = DrawSettings.ActiveUITheme.ButtonTheme;
			button.font = FontType.OpenSansBold;
			button.fontSize = 1.35f;
			button.buttonCols = new ButtonTheme.StateCols(Color.clear, Color.clear, Color.clear, Color.clear);
			Color label = primary ? Palette.Background : Palette.TextPrimary;
			button.textCols = new ButtonTheme.StateCols(label, label, label, Palette.TextDisabled);
			return UI.Button(text, button, pos, size, true, false, false, Anchor.TopLeft);
		}

		static void OpenHomeProjects()
		{
			selectedProjectIndex = -1;
			activeMenuScreen = MenuScreen.LoadProject;
		}

		static void DrawHome()
		{
			float rail = 18f;
			UI.DrawPanel(new Vector2(0, UI.Height), new Vector2(rail, UI.Height), Palette.Surface, Anchor.TopLeft);
			HomeSurface(new Vector2(2, UI.Height - 2.5f), new Vector2(3.4f, 3.4f), Color.black, 0.9f);
			HomeText("Tb", new Vector2(2.65f, UI.Height - 3.15f), 1.65f, Color.white, true);
			HomeText("Terbium", new Vector2(6.3f, UI.Height - 2.7f), 1.4f, Palette.TextPrimary, true);
			HomeText("Circuit simulator", new Vector2(6.3f, UI.Height - 5f), 0.85f, Palette.TextSecondary);

			float navY = UI.Height - 10f;
			HomeSurface(new Vector2(1.3f, navY), new Vector2(15.4f, 3.8f), Color.Lerp(Palette.Surface, Palette.Accent, 0.15f));
			HomeText("Workspace", new Vector2(3, navY - 1f), 1.4f, Palette.TextPrimary, true);
			if (HomeButton("All projects", new Vector2(1.3f, navY - 4.8f), new Vector2(15.4f, 3.8f))) OpenHomeProjects();
			if (HomeButton("Settings", new Vector2(1.3f, 13.8f), new Vector2(15.4f, 3.6f)) ||
				(activePopup == PopupKind.None && KeyboardShortcuts.MainMenu_SettingsShortcutTriggered))
			{
				EditedAppSettings = Main.ActiveAppSettings;
				activeMenuScreen = MenuScreen.Settings;
				OnSettingsMenuOpened();
			}
			if (HomeButton("About Terbium", new Vector2(1.3f, 9.4f), new Vector2(15.4f, 3.6f))) activeMenuScreen = MenuScreen.About;
			if (HomeButton("Quit", new Vector2(1.3f, 5f), new Vector2(15.4f, 3.6f)) ||
				(activePopup == PopupKind.None && KeyboardShortcuts.MainMenu_QuitShortcutTriggered)) Quit();

			float width = Mathf.Min(72f, UI.Width - rail - 8f);
			float left = rail + (UI.Width - rail - width) / 2;
			float top = UI.Height - 3.3f;
			HomeText("Workspace", new Vector2(left, top), 1.25f, Palette.TextSecondary);
			HomeText(versionString, new Vector2(left + width - 4.2f, top), 1.1f, Palette.TextSecondary);
			float y = top - 5f;
			HomeText("Your projects", new Vector2(left, y), Mathf.Min(2.4f, width / 16f), Palette.TextPrimary, true);
			y = UI.PrevBounds.Bottom - 1.2f;
			HomeText("Create and simulate ternary logic circuits.", new Vector2(left, y), 1.4f, Palette.TextSecondary);
			y = UI.PrevBounds.Bottom - 3f;

			float gap = 1.8f;
			float cardWidth = (width - gap) / 2;
			bool create = HomeActionCard(new Vector2(left, y), cardWidth, true);
			bool open = HomeActionCard(new Vector2(left + cardWidth + gap, y), cardWidth, false);
			if (activePopup == PopupKind.None)
			{
				if (create || KeyboardShortcuts.MainMenu_NewProjectShortcutTriggered) activePopup = PopupKind.NamePopup_NewProject;
				else if (open || KeyboardShortcuts.MainMenu_OpenProjectShortcutTriggered) OpenHomeProjects();
			}
			y -= 15f;
			HomeText("Recent projects", new Vector2(left, y), 1.75f, Palette.TextPrimary, true);
			y = UI.PrevBounds.Bottom - 1.8f;
			int count = Mathf.Min(allProjectDescriptions.Length, Mathf.Max(0, Mathf.FloorToInt((y - 3f) / 5.8f)));
			if (allProjectDescriptions.Length == 0)
			{
				HomeText("No projects yet. Create a project to get started.", new Vector2(left, y), 1.35f, Palette.TextSecondary);
			}
			for (int i = 0; i < count; i++)
			{
				Vector2 pos = new(left, y);
				HomeSurface(pos, new Vector2(width, 5f), Palette.Surface, 0.65f);
				HomeSurface(pos + new Vector2(1.1f, -0.9f), new Vector2(3.2f, 3.2f), Palette.SurfaceHover, 0.5f);
				HomeText("T", pos + new Vector2(2.05f, -1.45f), 1.5f, Palette.Accent, true);
				HomeText(allProjectDescriptions[i].ProjectName, pos + new Vector2(5.4f, -0.8f), 1.45f, Palette.TextPrimary, true);
				HomeText("Circuit project", pos + new Vector2(5.4f, -2.9f), 1.05f, Palette.TextSecondary);
				if (HomeButton(projectCompatibilities[i].compatible ? "Open" : "Details", pos + new Vector2(width - 8.5f, -0.8f), new Vector2(7.5f, 3.4f)))
				{
					if (projectCompatibilities[i].compatible) Main.CreateOrLoadProject(allProjectDescriptions[i].ProjectName, string.Empty);
					else { activeMenuScreen = MenuScreen.LoadProject; selectedProjectIndex = i; }
				}
				y -= 5.8f;
			}
		}

		static bool HomeActionCard(Vector2 pos, float width, bool primary)
		{
			HomeSurface(pos, new Vector2(width, 11.5f), Palette.Surface, 0.5f);
			HomeText(primary ? "New project" : "Open a project", pos + new Vector2(2, -1.6f),
				1.8f, Palette.TextPrimary, true);
			float descriptionTop = UI.PrevBounds.Bottom - 1f;
			HomeText(primary ? "Start a new circuit design." : "Continue an existing design.",
				new Vector2(pos.x + 2, descriptionTop), 1.3f, Palette.TextSecondary);
			return HomeButton(primary ? "Create project" : "Browse projects",
				pos + new Vector2(2, -7.3f), new Vector2(width - 4, 3.1f), primary);
		}

	}
}
