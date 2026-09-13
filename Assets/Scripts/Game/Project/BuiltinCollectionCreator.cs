using System.Linq;
using DLS.Description;

namespace DLS.Game
{
	public static class BuiltinCollectionCreator
	{
		public static StarredItem[] GetDefaultStarredList()
		{
			return new StarredItem[]
			{
				new("IN/OUT", true),
				new(ChipTypeHelper.GetName(ChipType.Not), false),
				new(ChipTypeHelper.GetName(ChipType.Min), false),
				new(ChipTypeHelper.GetName(ChipType.Max), false)
			};
		}

		public static ChipCollection[] CreateDefaultChipCollections()
		{
			return new[]
			{
				CreateChipCollection("BASIC",
					ChipType.Not,
					ChipType.Min,
					ChipType.Max,
					ChipType.Clock,
					ChipType.Pulse,
					ChipType.Key,
					ChipType.TriStateBuffer
				),
				CreateChipCollection("UNARY",
					ChipType.Not, ChipType.Buf, ChipType.PNot, ChipType.NNot, ChipType.Abs, ChipType.Clu, ChipType.Cld, ChipType.Inc, ChipType.Dec, ChipType.Rtu, ChipType.Rtd, ChipType.Isp, ChipType.Isz, ChipType.Isn
				),
				CreateChipCollection("BINARY",
					ChipType.Min, ChipType.Max, ChipType.Nand, ChipType.And, ChipType.Or, ChipType.Nor, ChipType.Cons, ChipType.NCons, ChipType.Any, ChipType.NAny, ChipType.Mul, ChipType.NMul, ChipType.Sum, ChipType.NSum
				),
				CreateChipCollection("MEMORY", ChipType.Rom_19683x9),
				CreateChipCollection("IN/OUT",
					ChipType.In_1Trit,
					ChipType.In_3Trit,
					ChipType.In_9Trit,
					ChipType.Out_1Trit,
					ChipType.Out_3Trit,
					ChipType.Out_9Trit
				),
				CreateChipCollection("MERGE/SPLIT",
					ChipType.Merge_1To3Trit,
					ChipType.Merge_1To9Trit,
					ChipType.Merge_3To9Trit,
					ChipType.Split_3To1Trit,
					ChipType.Split_9To3Trit,
					ChipType.Split_9To1Trit
				),
				CreateChipCollection("BUS",
					ChipType.Bus_1Trit,
					ChipType.Bus_3Trit,
					ChipType.Bus_9Trit
				),
				CreateChipCollection("LEGACY DISPLAY",
					ChipType.SevenSegmentDisplay,
					ChipType.DisplayDot,
					ChipType.DisplayRGB,
					ChipType.DisplayLED
				),
				CreateChipCollection("LEGACY MEMORY",
					ChipType.Rom_256x16
				),
				CreateChipCollection("LEGACY OTHER",
					ChipType.Buzzer
				)
			};
		}

		static ChipCollection CreateChipCollection(string name, params ChipType[] chipTypes)
		{
			return new ChipCollection(name, chipTypes.Select(t => ChipTypeHelper.GetName(t)).ToArray());
		}
	}
}
