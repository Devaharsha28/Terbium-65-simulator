using System;
using UnityEngine;

namespace DLS.Graphics
{
	/// <summary>
	/// A flat data class storing all semantic colors for the Terbium IDE theme.
	/// </summary>
	[Serializable]
	public class ThemePalette
	{
		// ---- Interface ----
		public string Background    = "#121417";
		public string Workspace     = "#1C1E23";
		public string Panel         = "#26292E";
		public string PanelElevated = "#31343A";
		public string Border        = "#4C5059";
		public string Accent        = "#4C8DFF";
		public string AccentHover   = "#6A9EFF";
		public string TextPrimary   = "#F5F7FA";
		public string TextSecondary = "#A4ADB5";
		public string TextDisabled  = "#707780";

		// ---- Semantic UI ----
		public string Success = "#4CAF7A";
		public string Warning = "#EBC870";
		public string Error   = "#D65A5A";

		// ---- Ternary Logic ----
		public string TritNegative = "#FF6B6B";
		public string TritZero     = "#858B93";
		public string TritPositive = "#5B9FE3";

		/// <summary>
		/// Returns a deep copy of this palette.
		/// </summary>
		public ThemePalette Clone() => (ThemePalette)MemberwiseClone();

		/// <summary>
		/// Parses a HEX color string to a Unity Color. Returns magenta on failure.
		/// </summary>
		public static Color Parse(string hex)
		{
			if (ColorUtility.TryParseHtmlString(hex.StartsWith("#") ? hex : "#" + hex, out Color c))
				return c;
			return Color.magenta;
		}

		/// <summary>
		/// Converts a Unity Color back to a 6-digit HEX string (e.g. "#4C8DFF").
		/// </summary>
		public static string ToHex(Color c) => "#" + ColorUtility.ToHtmlStringRGB(c);
	}
}
