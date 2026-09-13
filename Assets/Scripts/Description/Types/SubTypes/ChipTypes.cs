namespace DLS.Description
{
	public enum ChipType
	{
		Custom,

		// ---- Basic Chips ----
		Nand,
		Not,
		Min,
		Max,
		TriStateBuffer,
		Clock,
		Pulse,

		// ---- Memory ----
		dev_Ram_8Bit,
		Rom_256x16,

		// ---- Displays ----
		SevenSegmentDisplay,
		DisplayRGB,
		DisplayDot,
		DisplayLED,

		// ---- Merge / Split ----
		Merge_1To3Trit,
		Merge_1To9Trit,
		Merge_3To9Trit,
		Split_3To1Trit,
		Split_9To3Trit,
		Split_9To1Trit,

		// ---- In / Out Pins ----
		In_1Trit,
		In_3Trit,
		In_9Trit,
		Out_1Trit,
		Out_3Trit,
		Out_9Trit,

		Key,

		// ---- Buses ----
		Bus_1Trit,
		BusTerminus_1Trit,
		Bus_3Trit,
		BusTerminus_3Trit,
		Bus_9Trit,
		BusTerminus_9Trit,
		
		// ---- Audio ----
		Buzzer,

		// Append types to preserve serialized IDs of existing components.
		Buf,
		PNot,
		NNot,
		Abs,
		Clu,
		Cld,
		Inc,
		Dec,
		Rtu,
		Rtd,
		Isp,
		Isz,
		Isn,
		And,
		Or,
		Nor,
		Cons,
		NCons,
		Any,
		NAny,
		Mul,
		NMul,
		Sum,
		NSum,
		Rom_19683x9

	}
}
