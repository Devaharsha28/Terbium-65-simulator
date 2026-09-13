using UnityEngine;

namespace DLS.Description
{
	public struct PinDescription
	{
		public string Name;
		public int ID;
		public Vector2 Position;
		public PinTritCount TritCount;
		public PinColour Colour;
		public PinValueDisplayMode ValueDisplayMode;

		public PinDescription(string name, int id, Vector2 position, PinTritCount tritCount, PinColour colour, PinValueDisplayMode valueDisplayMode)
		{
			Name = name;
			ID = id;
			Position = position;
			TritCount = tritCount;
			Colour = colour;
			ValueDisplayMode = valueDisplayMode;
		}
	}

	public enum PinTritCount
	{
		Trit1 = 1,
		Trit3 = 3,
		Trit9 = 9
	}

	public enum PinColour
	{
		Red,
		Orange,
		Yellow,
		Green,
		Blue,
		Violet,
		Pink,
		White
	}

	public enum PinValueDisplayMode
	{
		Off,
		Ternary,
		Decimal,
		Nonary,
		Hept
	}
}