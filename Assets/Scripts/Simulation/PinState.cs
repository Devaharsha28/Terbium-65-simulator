namespace DLS.Simulation
{
	// Helper class for dealing with pin state.
	// Pin state is stored as a uint32, with format:
	// Logic: bits 0..17 (two per trit). Disconnected: bits 18..26.
	public static class PinState
	{
		// Mask for single trit value (2 logic bits, and 1 tristate flag)
		public const uint SingleTritMask = 3u | (1u << 18);
		
		public static uint GetBitStates(uint state) => state & 0x3FFFFu; // Bottom 18 bits
		public static uint GetTristateFlags(uint state) => (state >> 18) & 0x1FFu;

		public static void Set(ref uint state, uint bitStates, uint tristateFlags)
		{
			state = (bitStates & 0x3FFFFu) | ((tristateFlags & 0x1FFu) << 18);
		}

		public static void Set(ref uint state, uint other) => state = other;

		public static bool FirstBitHigh(uint state) => !IsTritAtIndexDisconnected(state, 0) && GetTritAtIndex(state, 0) == TritPositive;

		public static void Set3TritFrom9TritSource(ref uint state, uint source9trit, int groupIndex)
		{
			uint sourceBitStates = GetBitStates(source9trit);
			uint sourceTristateFlags = GetTristateFlags(source9trit);

			// groupIndex 0: bottom 3 trits (6 logic bits, 3 flag bits)
			// groupIndex 1: middle 3 trits
			// groupIndex 2: top 3 trits
			uint logicMask = 0b111111u << (groupIndex * 6);
			uint flagMask = 0b111u << (groupIndex * 3);

			Set(ref state, (sourceBitStates & logicMask) >> (groupIndex * 6), (sourceTristateFlags & flagMask) >> (groupIndex * 3));
		}

		public static void Set9TritFrom3TritSources(ref uint state, uint a, uint b, uint c)
		{
			uint bitStates = (GetBitStates(a) & 63u) | ((GetBitStates(b) & 63u) << 6) | ((GetBitStates(c) & 63u) << 12);
			uint tristateFlags = (GetTristateFlags(a) & 0b111) | ((GetTristateFlags(b) & 0b111) << 3) | ((GetTristateFlags(c) & 0b111) << 6);
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

		public static void SetAllDisconnected(ref uint state) => state |= 0x1FFu << 18;

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
			uint flagShift = (uint)(18 + tritIndex);
			
			// Clear the logic bits and the disconnected flag
			state &= ~( (3u << (int)logicShift) | (1u << (int)flagShift) );
			// Set the logic bits
			state |= (TritToUint(trit) << (int)logicShift);
		}

		public static bool IsTritAtIndexDisconnected(uint state, int tritIndex)
		{
			uint flagShift = (uint)(18 + tritIndex);
			return (state & (1u << (int)flagShift)) != 0;
		}

		public static void SetTritAtIndexDisconnected(ref uint state, int tritIndex)
		{
			uint flagShift = (uint)(18 + tritIndex);
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

		public static bool HasDisconnectedTrit(uint state, int count) =>
			(GetTristateFlags(state) & ((1u << count) - 1)) != 0;

		public static int FormatTernary(uint state, int count, char[] buffer)
		{
			for (int i = 0; i < count; i++)
			{
				int index = count - 1 - i;
				buffer[i] = IsTritAtIndexDisconnected(state, index) ? 'Z' :
					GetTritAtIndex(state, index) < 0 ? '-' : GetTritAtIndex(state, index) > 0 ? '+' : '0';
			}
			return count;
		}

		// Encode a signed nine-trit value; packed zero is -9841, not numeric zero.
		public static uint FromDecimal9(int value)
		{
			if (value < -9841 || value > 9841) throw new System.ArgumentOutOfRangeException(nameof(value));
			uint state = 0;
			int digits = value + 9841;
			for (int i = 0; i < 9; i++, digits /= 3) SetTritAtIndex(ref state, i, (sbyte)(digits % 3 - 1));
			return state;
		}

		public static uint[] CreateRom9Data(uint[] source = null)
		{
			uint[] data = new uint[19683];
			for (int i = 0; i < data.Length; i++) data[i] = FromDecimal9(0);
			if (source != null) System.Array.Copy(source, data, System.Math.Min(source.Length, data.Length));
			return data;
		}

		public static int FormatGrouped(uint state, int count, int groupSize, char[] buffer)
		{
			if (groupSize != 2 && groupSize != 3) throw new System.ArgumentOutOfRangeException(nameof(groupSize));
			int groups = (count + groupSize - 1) / groupSize;
			int length = 0;
			for (int g = groups - 1; g >= 0; g--)
			{
				if (groupSize == 3 && g != groups - 1) buffer[length++] = ' ';
				int value = 0, weight = 1;
				bool disconnected = false;
				for (int i = 0; i < groupSize; i++, weight *= 3)
				{
					int index = g * groupSize + i;
					if (index >= count) continue; // Pad missing high trits with numeric zero.
					value += GetTritAtIndex(state, index) * weight;
					disconnected |= IsTritAtIndexDisconnected(state, index);
				}
				if (disconnected) buffer[length++] = '?';
				else if (value < 0) buffer[length++] = (char)('a' + (-value - 1));
				else
				{
					if (value >= 10) buffer[length++] = '1';
					buffer[length++] = (char)('0' + value % 10);
				}
			}
			return length;
		}
	}
}
