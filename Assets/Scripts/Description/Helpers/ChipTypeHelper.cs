using System;
using System.Collections.Generic;

namespace DLS.Description
{
	public static class ChipTypeHelper
	{
		const string mulSymbol = "\u00d7";

		static readonly Dictionary<ChipType, string> Names = new()
		{
			// ---- Basic Chips ----
			{ ChipType.Buf, "BUF" },
			{ ChipType.PNot, "PNOT" },
			{ ChipType.NNot, "NNOT" },
			{ ChipType.Abs, "ABS" },
			{ ChipType.Clu, "CLU" },
			{ ChipType.Cld, "CLD" },
			{ ChipType.Inc, "INC" },
			{ ChipType.Dec, "DEC" },
			{ ChipType.Rtu, "RTU" },
			{ ChipType.Rtd, "RTD" },
			{ ChipType.Isp, "ISP" },
			{ ChipType.Isz, "ISZ" },
			{ ChipType.Isn, "ISN" },
			{ ChipType.And, "AND" },
			{ ChipType.Or, "OR" },
			{ ChipType.Nor, "NOR" },
			{ ChipType.Cons, "CONS" },
			{ ChipType.NCons, "NCONS" },
			{ ChipType.Any, "ANY" },
			{ ChipType.NAny, "NANY" },
			{ ChipType.Mul, "MUL" },
			{ ChipType.NMul, "NMUL" },
			{ ChipType.Sum, "SUM" },
			{ ChipType.NSum, "NSUM" },
			{ ChipType.Rom_19683x9, "ROM 19683x9" },
			{ ChipType.Nand, "NAND" },
			{ ChipType.Not, "NOT" },
			{ ChipType.Min, "MIN" },
			{ ChipType.Max, "MAX" },
			{ ChipType.Clock, "CLOCK" },
			{ ChipType.Pulse, "PULSE" },
			{ ChipType.TriStateBuffer, "3-STATE BUFFER" },
			// ---- Memory ----
			{ ChipType.dev_Ram_8Bit, "dev.RAM-8" },
			{ ChipType.Rom_256x16, $"ROM 256{mulSymbol}16" },
			// ---- Split / Merge ----
			{ ChipType.Split_3To1Trit, "3-1TRIT" },
			{ ChipType.Split_9To1Trit, "9-1TRIT" },
			{ ChipType.Split_9To3Trit, "9-3TRIT" },
			{ ChipType.Merge_3To9Trit, "3-9TRIT" },
			{ ChipType.Merge_1To9Trit, "1-9TRIT" },
			{ ChipType.Merge_1To3Trit, "1-3TRIT" },

			// ---- Displays -----
			{ ChipType.DisplayRGB, "RGB DISPLAY" },
			{ ChipType.DisplayDot, "DOT DISPLAY" },
			{ ChipType.SevenSegmentDisplay, "7-SEGMENT" },
			{ ChipType.DisplayLED, "LED" },

			{ ChipType.Buzzer, "BUZZER" },

			// ---- Not really chips (but convenient to treat them as such anyway) ----

			// ---- Inputs/Outputs ----
			{ ChipType.In_1Trit, "IN-1" },
			{ ChipType.In_3Trit, "IN-3" },
			{ ChipType.In_9Trit, "IN-9" },
			{ ChipType.Out_1Trit, "OUT-1" },
			{ ChipType.Out_3Trit, "OUT-3" },
			{ ChipType.Out_9Trit, "OUT-9" },
			{ ChipType.Key, "KEY" },
			// ---- Buses ----
			{ ChipType.Bus_1Trit, "BUS-1" },
			{ ChipType.Bus_3Trit, "BUS-3" },
			{ ChipType.Bus_9Trit, "BUS-9" },
			{ ChipType.BusTerminus_1Trit, "BUS-TERMINUS-1" },
			{ ChipType.BusTerminus_3Trit, "BUS-TERMINUS-3" },
			{ ChipType.BusTerminus_9Trit, "BUS-TERMINUS-9" }
		};

		public static string GetName(ChipType type) => Names[type];

		public static bool IsBusType(ChipType type) => IsBusOriginType(type) || IsBusTerminusType(type);

		public static bool IsBusOriginType(ChipType type) => type is ChipType.Bus_1Trit or ChipType.Bus_3Trit or ChipType.Bus_9Trit;

		public static bool IsBusTerminusType(ChipType type) => type is ChipType.BusTerminus_1Trit or ChipType.BusTerminus_3Trit or ChipType.BusTerminus_9Trit;

		public static bool IsRomType(ChipType type) => type is ChipType.Rom_256x16 or ChipType.Rom_19683x9;

		public static ChipType GetCorrespondingBusTerminusType(ChipType type)
		{
			return type switch
			{
				ChipType.Bus_1Trit => ChipType.BusTerminus_1Trit,
				ChipType.Bus_3Trit => ChipType.BusTerminus_3Trit,
				ChipType.Bus_9Trit => ChipType.BusTerminus_9Trit,
				_ => throw new Exception("No corresponding bus terminus found for type: " + type)
			};
		}

		public static ChipType GetPinType(bool isInput, PinTritCount numBits)
		{
			if (isInput)
			{
				return numBits switch
				{
					PinTritCount.Trit1 => ChipType.In_1Trit,
					PinTritCount.Trit3 => ChipType.In_3Trit,
					PinTritCount.Trit9 => ChipType.In_9Trit,
					_ => throw new Exception("No input pin type found for tritcount: " + numBits)
				};
			}

			return numBits switch
			{
				PinTritCount.Trit1 => ChipType.Out_1Trit,
				PinTritCount.Trit3 => ChipType.Out_3Trit,
				PinTritCount.Trit9 => ChipType.Out_9Trit,
				_ => throw new Exception("No output pin type found for tritcount: " + numBits)
			};
		}

		public static (bool isInput, bool isOutput, PinTritCount numBits) IsInputOrOutputPin(ChipType type)
		{
			return type switch
			{
				ChipType.In_1Trit => (true, false, PinTritCount.Trit1),
				ChipType.Out_1Trit => (false, true, PinTritCount.Trit1),
				ChipType.In_3Trit => (true, false, PinTritCount.Trit3),
				ChipType.Out_3Trit => (false, true, PinTritCount.Trit3),
				ChipType.In_9Trit => (true, false, PinTritCount.Trit9),
				ChipType.Out_9Trit => (false, true, PinTritCount.Trit9),
				_ => (false, false, PinTritCount.Trit1)
			};
		}
	}
}
