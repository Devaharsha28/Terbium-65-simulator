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
		// Layered neutral surfaces keep attention on the circuit, while the
		// blue accent is reserved for focus, selection and primary actions.
		public string Background    = "#191919";
		public string Workspace     = "#222222";
		public string Panel         = "#292929";
		public string PanelElevated = "#333333";
		public string Border        = "#454545";
		public string Accent        = "#86AED4";
		public string AccentHover   = "#A2C1DF";
		public string TextPrimary   = "#E6E6E6";
		public string TextSecondary = "#AFB5BE";
		public string TextDisabled  = "#767E89";

		// ---- Semantic UI ----
		public string Success = "#83B69A";
		public string Warning = "#D6B77D";
		public string Error   = "#FF4040";

		// ---- Ternary Logic ----
		public string TritNegative = "#FF0000";
		public string TritZero     = "#FFFFFF";
		public string TritPositive = "#00B8F0";

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
