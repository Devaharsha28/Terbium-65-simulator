namespace DLS.Simulation
{
	// Helper class for dealing with pin state.
	// Pin state is stored as a uint32, with format:
	// Tristate flags (most significant 16 bits) | Bit states (least significant 16 bits)
	public static class PinState
	{
		// Each bit has three possible states (tri-state logic):
		public const ushort LogicLow = 0;
		public const ushort LogicHigh = 1;
		public const ushort LogicDisconnected = 2;

		// Mask for single trit value (2 logic bits, and 1 tristate flag)
		public const uint SingleTritMask = 3u | (1u << 16);
		
		public static ushort GetBitStates(uint state) => (ushort)state;
		public static ushort GetTristateFlags(uint state) => (ushort)(state >> 16);

		public static void Set(ref uint state, ushort bitStates, ushort tristateFlags)
		{
			state = (uint)(bitStates | (tristateFlags << 16));
		}

		public static void Set(ref uint state, uint other) => state = other;

		public static bool FirstBitHigh(uint state) => !IsTritAtIndexDisconnected(state, 0) && GetTritAtIndex(state, 0) == TritPositive;

		public static void Set4BitFrom8BitSource(ref uint state, uint source8bit, bool firstNibble)
		{
			ushort sourceBitStates = GetBitStates(source8bit);
			ushort sourceTristateFlags = GetTristateFlags(source8bit);

			if (firstNibble)
			{
				const ushort logicMask = 0b11111111; // 8 bits (4 trits)
				const ushort flagMask = 0b1111;      // 4 bits (4 flags)
				Set(ref state, (ushort)(sourceBitStates & logicMask), (ushort)(sourceTristateFlags & flagMask));
			}
			else
			{
				const ushort logicMask = 0b1111111100000000;
				const ushort flagMask = 0b11110000;
				Set(ref state, (ushort)((sourceBitStates & logicMask) >> 8), (ushort)((sourceTristateFlags & flagMask) >> 4));
			}
		}

		public static void Set8BitFrom4BitSources(ref uint state, uint a, uint b)
		{
			ushort bitStates = (ushort)(GetBitStates(a) | (GetBitStates(b) << 8));
			ushort tristateFlags = (ushort)((GetTristateFlags(a) & 0b1111) | ((GetTristateFlags(b) & 0b1111) << 4));
			Set(ref state, bitStates, tristateFlags);
		}


		public static void Toggle(ref uint state, int tritIndex)
		{
			sbyte currentTrit = GetTritAtIndex(state, tritIndex);
			sbyte nextTrit = currentTrit switch
			{
				-1 => 0,
				0 => 1,
				1 => -1,
				_ => -1
			};
			SetTritAtIndex(ref state, tritIndex, nextTrit);
		}

		public static void SetAllDisconnected(ref uint state) => Set(ref state, 0, ushort.MaxValue);

		// ---- Ternary (Balanced Ternary) Representation ----
		// For single-trit operation, we use sbyte representation:
		// -1 = negative logic
		// 0 = zero logic
		// +1 = positive logic

		public const sbyte TritNegative = -1;
		public const sbyte TritZero = 0;
		public const sbyte TritPositive = 1;

		// Convert ternary sbyte to uint for logic state
		// Maps: -1 -> 0, 0 -> 1, +1 -> 2
		public static uint TritToUint(sbyte trit)
		{
			return trit switch
			{
				TritNegative => 0,
				TritZero => 1,
				TritPositive => 2,
				_ => 1 // Default to zero for unknown values
			};
		}

		// Convert uint logic bits back to ternary sbyte
		public static sbyte UintToTrit(uint value)
		{
			return (value & 3) switch
			{
				0 => TritNegative,
				1 => TritZero,
				2 => TritPositive,
				_ => TritZero
			};
		}

		// Get ternary value from uint state (logic value only)
		public static sbyte GetTritValue(uint state)
		{
			return UintToTrit(state);
		}

		// Set ternary value in uint state (and set it as connected)
		public static void SetTritValue(ref uint state, sbyte trit)
		{
			SetTritAtIndex(ref state, 0, trit);
		}

		// Set disconnected state for ternary
		public static void SetTritDisconnected(ref uint state)
		{
			SetTritAtIndexDisconnected(ref state, 0);
		}

		// Check if ternary state is disconnected
		public static bool IsTritDisconnected(uint state)
		{
			return IsTritAtIndexDisconnected(state, 0);
		}

		// ---- Multi-trit Generalized Helpers ----

		public static sbyte GetTritAtIndex(uint state, int tritIndex)
		{
			uint shift = (uint)(tritIndex * 2);
			uint logicBits = (state >> (int)shift) & 3u;
			return UintToTrit(logicBits);
		}

		public static void SetTritAtIndex(ref uint state, int tritIndex, sbyte trit)
		{
			uint logicShift = (uint)(tritIndex * 2);
			uint flagShift = (uint)(16 + tritIndex);
			
			// Clear the logic bits and the disconnected flag
			state &= ~( (3u << (int)logicShift) | (1u << (int)flagShift) );
			// Set the logic bits
			state |= (TritToUint(trit) << (int)logicShift);
		}

		public static bool IsTritAtIndexDisconnected(uint state, int tritIndex)
		{
			uint flagShift = (uint)(16 + tritIndex);
			return (state & (1u << (int)flagShift)) != 0;
		}

		public static void SetTritAtIndexDisconnected(ref uint state, int tritIndex)
		{
			uint flagShift = (uint)(16 + tritIndex);
			state |= (1u << (int)flagShift);
		}

		public static int GetTernaryDecimalValue(uint state, int numTrits)
		{
			int displayValue = 0;
			int weight = 1;
			for (int i = 0; i < numTrits; i++)
			{
				sbyte trit = GetTritAtIndex(state, i);
				displayValue += trit * weight;
				weight *= 3;
			}
			return displayValue;
		}
	}
}