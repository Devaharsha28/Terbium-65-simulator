using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using DLS.Description;
using DLS.Game;
using Random = System.Random;

namespace DLS.Simulation
{
	public static class Simulator
	{
		public static readonly Random rng = new();
		static readonly Stopwatch stopwatch = Stopwatch.StartNew();
		public static int stepsPerClockTransition;
		public static int simulationFrame;
		static uint pcg_rngState;

		// When sim is first built, or whenever modified, it needs to run a less efficient pass in which the traversal order of the chips is determined
		public static bool needsOrderPass;

		// Every n frames the simulation permits some random modifications to traversal order of sequential chips (to randomize outcome of race conditions)
		public static bool canDynamicReorderThisFrame;

		static SimChip prevRootSimChip;
		static double elapsedSecondsOld;
		static double deltaTime;
		static SimAudio audioState;

		// Modifications to the sim are made from the main thread, but only applied on the sim thread to avoid conflicts
		static readonly ConcurrentQueue<SimModifyCommand> modificationQueue = new();

		// ---- Simulation outline ----
		// 1) Forward the initial player-controlled input states to all connected pins.
		// 2) Loop over all subchips not yet processed this frame, and process them if they are ready (i.e. all input pins have received all their inputs)
		//    * Note: this means that the input pins must be aware of how many input connections they have (pins choose randomly between conflicting inputs)
		//    * Note: if a pin has zero input connections, it should be considered as always ready
		// 3) Forward the outputs of the processed subchips to their connected pins, and repeat steps 2 & 3 until no more subchips are ready for processing.
		// 4) If all subchips have now been processed, then we're done. This is not necessarily the case though, since if an input pin depends on the output of its parent chip
		//    (directly or indirectly), then it won't receive all its inputs until the chip has already been run, meaning that the chip must be processed before it is ready.
		//    In this case we process one of the remaining unprocessed (and non-ready) subchips at random, and return to step 3.
		//
		// Optimization ideas (todo):
		// * Compute lookup table for combinational chips
		// * Ignore chip if inputs are same as last frame, and no internal pins changed state last frame.
		//   (would have to make exception for chips containing things like clock or key chip, which can activate 'spontaneously')
		// * Create simplified connections network allowing only builtin chips to be processed during simulation

		public static void RunSimulationStep(SimChip rootSimChip, DevPinInstance[] inputPins, SimAudio audioState)
		{
			Simulator.audioState = audioState;
			audioState.InitFrame();

			if (rootSimChip != prevRootSimChip)
			{
				needsOrderPass = true;
				prevRootSimChip = rootSimChip;
			}

			pcg_rngState = (uint)rng.Next();
			canDynamicReorderThisFrame = simulationFrame % 100 == 0;
			simulationFrame++; //

			// Step 1) Get player-controlled input states and copy values to the sim
			foreach (DevPinInstance input in inputPins)
			{
				try
				{
					SimPin simPin = rootSimChip.GetSimPinFromAddress(input.Pin.Address);
					PinState.Set(ref simPin.State, input.Pin.PlayerInputState);

					input.Pin.State = input.Pin.PlayerInputState;
				}
				catch (Exception)
				{
					// Possible for sim to be temporarily out of sync since running on separate threads, so just ignore failure to find pin.
				}
			}

			// Process
			if (needsOrderPass)
			{
				StepChipReorder(rootSimChip);
				needsOrderPass = false;
			}
			else
			{
				StepChip(rootSimChip);
			}

			UpdateAudioState();
		}

		public static void UpdateInPausedState()
		{
			if (audioState != null)
			{
				audioState.InitFrame();
				UpdateAudioState();
			}
		}

		static void UpdateAudioState()
		{
			double elapsedSeconds = stopwatch.Elapsed.TotalSeconds;
			if (simulationFrame <= 1) deltaTime = 0;
			else deltaTime = elapsedSeconds - elapsedSecondsOld;
			elapsedSecondsOld = stopwatch.Elapsed.TotalSeconds;
			audioState.NotifyAllNotesRegistered(deltaTime);
		}

		// Recursively propagate signals through this chip and its subchips
		static void StepChip(SimChip chip)
		{
			// Propagate signal from all input dev-pins to all their connected pins
			chip.Sim_PropagateInputs();

			// NOTE: subchips are assumed to have been sorted in reverse order of desired visitation
			for (int i = chip.SubChips.Length - 1; i >= 0; i--)
			{
				SimChip nextSubChip = chip.SubChips[i];

				// Every n frames (for performance reasons) the simulation permits some random modifications to the chip traversal order.
				// Here two chips may be swapped if they are not 'ready' (i.e. all inputs have not yet been received for this
				// frame; indicating that the input relies on the output). The purpose of this reordering is to allow some variety in
				// the outcomes of race-conditions (such as an SR latch having both inputs enabled, and then released).
				if (canDynamicReorderThisFrame && i > 0 && !nextSubChip.Sim_IsReady() && RandomBool())
				{
					SimChip potentialSwapChip = chip.SubChips[i - 1];
					if (!ChipTypeHelper.IsBusOriginType(potentialSwapChip.ChipType))
					{
						nextSubChip = potentialSwapChip;
						(chip.SubChips[i], chip.SubChips[i - 1]) = (chip.SubChips[i - 1], chip.SubChips[i]);
					}
				}

				if (nextSubChip.IsBuiltin) ProcessBuiltinChip(nextSubChip); // We've reached a built-in chip, so process it directly
				else StepChip(nextSubChip); // Recursively process custom chip

				// Step 3) Forward the outputs of the processed subchip to connected pins
				nextSubChip.Sim_PropagateOutputs();
			}
		}

		// Recursively propagate signals through this chip and its subchips
		// In the process, reorder all subchips based on order in which they become ready for processing (have received all their inputs)
		// Note: the order here is reversed, so those ready first will be at the end of the array
		static void StepChipReorder(SimChip chip)
		{
			chip.Sim_PropagateInputs();

			SimChip[] subChips = chip.SubChips;
			int numRemaining = subChips.Length;

			while (numRemaining > 0)
			{
				int nextSubChipIndex = ChooseNextSubChip(subChips, numRemaining);
				SimChip nextSubChip = subChips[nextSubChipIndex];

				// "Remove" the chosen subchip from remaining sub chips.
				// This is done by moving it to the end of the array and reducing the length of the span by one.
				// This also places the subchip into (reverse) order, so that the traversal order need to be determined again on the next pass.
				(subChips[nextSubChipIndex], subChips[numRemaining - 1]) = (subChips[numRemaining - 1], subChips[nextSubChipIndex]);
				numRemaining--;

				// Process chosen subchip
				if (nextSubChip.ChipType == ChipType.Custom) StepChipReorder(nextSubChip); // Recursively process custom chip
				else ProcessBuiltinChip(nextSubChip); // We've reached a built-in chip, so process it directly 

				// Step 3) Forward the outputs of the processed subchip to connected pins
				nextSubChip.Sim_PropagateOutputs();
			}
		}

		static int ChooseNextSubChip(SimChip[] subChips, int num)
		{
			bool noSubChipsReady = true;
			bool isNonBusChipRemaining = false;
			int nextSubChipIndex = -1;

			// Step 2) Loop over all subchips not yet processed this frame, and process them if they are ready
			for (int i = 0; i < num; i++)
			{
				SimChip subChip = subChips[i];
				if (subChip.Sim_IsReady())
				{
					noSubChipsReady = false;
					nextSubChipIndex = i;
					break;
				}

				isNonBusChipRemaining |= !ChipTypeHelper.IsBusOriginType(subChip.ChipType);
			}

			// Step 4) if no sub chip is ready to be processed, pick one at random (but save buses for last)
			if (noSubChipsReady)
			{
				nextSubChipIndex = rng.Next(0, num);

				// If processing in random order, save buses for last (since we must know all their inputs to display correctly)
				if (isNonBusChipRemaining)
				{
					for (int i = 0; i < num; i++)
					{
						if (!ChipTypeHelper.IsBusOriginType(subChips[nextSubChipIndex].ChipType)) break;
						nextSubChipIndex = (nextSubChipIndex + 1) % num;
					}
				}
			}

			return nextSubChipIndex;
		}

		public static void UpdateKeyboardInputFromMainThread()
		{
			SimKeyboardHelper.RefreshInputState();
		}

		public static bool RandomBool()
		{
			pcg_rngState = pcg_rngState * 747796405 + 2891336453;
			uint result = ((pcg_rngState >> (int)((pcg_rngState >> 28) + 4)) ^ pcg_rngState) * 277803737;
			result = (result >> 22) ^ result;
			return result < uint.MaxValue / 2;
		}

		static sbyte EvaluateUnary(ChipType type, int a) => (sbyte)(type switch
		{
			ChipType.Buf => a,
			ChipType.Not => -a,
			ChipType.PNot => a == 1 ? -1 : 1,
			ChipType.NNot => a == -1 ? 1 : -1,
			ChipType.Abs => Math.Abs(a),
			ChipType.Clu => Math.Max(a, 0),
			ChipType.Cld => Math.Min(a, 0),
			ChipType.Inc or ChipType.Rtu => a == 1 ? -1 : a + 1,
			ChipType.Dec or ChipType.Rtd => a == -1 ? 1 : a - 1,
			ChipType.Isp => a == 1 ? 1 : -1,
			ChipType.Isz => a == 0 ? 1 : -1,
			ChipType.Isn => a == -1 ? 1 : -1,
			_ => throw new ArgumentOutOfRangeException(nameof(type))
		});

		static sbyte EvaluateBinary(ChipType type, int a, int b)
		{
			int sum = a + b;
			int wrappedSum = sum > 1 ? sum - 3 : sum < -1 ? sum + 3 : sum;
			return (sbyte)(type switch
			{
				ChipType.Min or ChipType.And => Math.Min(a, b),
				ChipType.Nand => -Math.Min(a, b),
				ChipType.Max or ChipType.Or => Math.Max(a, b),
				ChipType.Nor => -Math.Max(a, b),
				ChipType.Cons => a == b ? a : 0,
				ChipType.NCons => a == b ? -a : 0,
				// The supplied ANY table equals MAX; keep distinct component IDs.
				ChipType.Any => Math.Max(a, b),
				ChipType.NAny => -Math.Max(a, b),
				ChipType.Mul => a * b,
				ChipType.NMul => -a * b,
				ChipType.Sum => wrappedSum,
				ChipType.NSum => -wrappedSum,
				_ => throw new ArgumentOutOfRangeException(nameof(type))
			});
		}

		static void ProcessBuiltinChip(SimChip chip)
		{
			switch (chip.ChipType)
			{
				// ---- Process Built-in chips ----
				case ChipType.Not:
				case ChipType.Buf:
				case ChipType.PNot:
				case ChipType.NNot:
				case ChipType.Abs:
				case ChipType.Clu:
				case ChipType.Cld:
				case ChipType.Inc:
				case ChipType.Dec:
				case ChipType.Rtu:
				case ChipType.Rtd:
				case ChipType.Isp:
				case ChipType.Isz:
				case ChipType.Isn:
				{
					uint input = chip.InputPins[0].State;
					if (PinState.IsTritDisconnected(input)) PinState.SetAllDisconnected(ref chip.OutputPins[0].State);
					else PinState.SetTritValue(ref chip.OutputPins[0].State, EvaluateUnary(chip.ChipType, PinState.GetTritValue(input)));
					break;
				}
				case ChipType.Min:
				case ChipType.Max:
				case ChipType.Nand:
				case ChipType.And:
				case ChipType.Or:
				case ChipType.Nor:
				case ChipType.Cons:
				case ChipType.NCons:
				case ChipType.Any:
				case ChipType.NAny:
				case ChipType.Mul:
				case ChipType.NMul:
				case ChipType.Sum:
				case ChipType.NSum:
				{
					uint a = chip.InputPins[0].State, b = chip.InputPins[1].State;
					if (PinState.IsTritDisconnected(a) || PinState.IsTritDisconnected(b))
						PinState.SetAllDisconnected(ref chip.OutputPins[0].State);
					else PinState.SetTritValue(ref chip.OutputPins[0].State,
						EvaluateBinary(chip.ChipType, PinState.GetTritValue(a), PinState.GetTritValue(b)));
					break;
				}
				case ChipType.Clock:
				{
					bool high = stepsPerClockTransition != 0 && ((simulationFrame / stepsPerClockTransition) & 1) == 0;
					uint state = 0;
					PinState.SetTritValue(ref state, high ? PinState.TritPositive : PinState.TritZero);
					chip.OutputPins[0].State = state;
					break;
				}
				case ChipType.Pulse:
				{
					const int pulseDurationIndex = 0;
					const int pulseTicksRemainingIndex = 1;
					const int pulseInputOldIndex = 2;

					uint inputState = chip.InputPins[0].State;
					bool pulseInputHigh = PinState.FirstBitHigh(inputState);
					uint pulseTicksRemaining = chip.InternalState[pulseTicksRemainingIndex];

					if (pulseTicksRemaining == 0)
					{
						bool isRisingEdge = pulseInputHigh && chip.InternalState[pulseInputOldIndex] == 0;
						if (isRisingEdge)
						{
							pulseTicksRemaining = chip.InternalState[pulseDurationIndex];
							chip.InternalState[pulseTicksRemainingIndex] = pulseTicksRemaining;
						}
					}

					uint outputState = 0;
					PinState.SetTritValue(ref outputState, PinState.TritZero);
					if (pulseTicksRemaining > 0)
					{
						chip.InternalState[1]--;
						PinState.SetTritValue(ref outputState, PinState.TritPositive);
					}
					else if (PinState.IsTritDisconnected(inputState))
					{
						PinState.SetTritDisconnected(ref outputState);
					}

					chip.OutputPins[0].State = outputState;
					chip.InternalState[pulseInputOldIndex] = pulseInputHigh ? 1u : 0;

					break;
				}
				case ChipType.Split_3To1Trit:
				{
					uint inState = chip.InputPins[0].State;
					for (int i = 0; i < 3; i++)
					{
						uint outState = 0;
						PinState.SetTritAtIndex(ref outState, 0, PinState.GetTritAtIndex(inState, 2 - i));
						if (PinState.IsTritAtIndexDisconnected(inState, 2 - i)) PinState.SetTritAtIndexDisconnected(ref outState, 0);
						chip.OutputPins[i].State = outState;
					}
					break;
				}
				case ChipType.Merge_1To3Trit:
				{
					uint outState = 0;
					for (int i = 0; i < 3; i++)
					{
						uint inState = chip.InputPins[2 - i].State;
						PinState.SetTritAtIndex(ref outState, i, PinState.GetTritAtIndex(inState, 0));
						if (PinState.IsTritAtIndexDisconnected(inState, 0)) PinState.SetTritAtIndexDisconnected(ref outState, i);
					}
					chip.OutputPins[0].State = outState;
					break;
				}
				case ChipType.Merge_1To9Trit:
				{
					uint outState = 0;
					for (int i = 0; i < 9; i++)
					{
						uint inState = chip.InputPins[8 - i].State;
						PinState.SetTritAtIndex(ref outState, i, PinState.GetTritAtIndex(inState, 0));
						if (PinState.IsTritAtIndexDisconnected(inState, 0)) PinState.SetTritAtIndexDisconnected(ref outState, i);
					}
					chip.OutputPins[0].State = outState;
					break;
				}
				case ChipType.Merge_3To9Trit:
				{
					SimPin in3A = chip.InputPins[0];
					SimPin in3B = chip.InputPins[1];
					SimPin in3C = chip.InputPins[2];
					SimPin out9 = chip.OutputPins[0];
					PinState.Set9TritFrom3TritSources(ref out9.State, in3C.State, in3B.State, in3A.State);
					break;
				}
				case ChipType.Split_9To3Trit:
				{
					SimPin in9 = chip.InputPins[0];
					SimPin out3A = chip.OutputPins[0];
					SimPin out3B = chip.OutputPins[1];
					SimPin out3C = chip.OutputPins[2];
					PinState.Set3TritFrom9TritSource(ref out3A.State, in9.State, 2);
					PinState.Set3TritFrom9TritSource(ref out3B.State, in9.State, 1);
					PinState.Set3TritFrom9TritSource(ref out3C.State, in9.State, 0);
					break;
				}
				case ChipType.Split_9To1Trit:
				{
					uint inState = chip.InputPins[0].State;
					for (int i = 0; i < 9; i++)
					{
						uint outState = 0;
						PinState.SetTritAtIndex(ref outState, 0, PinState.GetTritAtIndex(inState, 8 - i));
						if (PinState.IsTritAtIndexDisconnected(inState, 8 - i)) PinState.SetTritAtIndexDisconnected(ref outState, 0);
						chip.OutputPins[i].State = outState;
					}
					break;
				}
				case ChipType.TriStateBuffer:
				{
					SimPin dataPin = chip.InputPins[0];
					SimPin enablePin = chip.InputPins[1];
					SimPin outputPin = chip.OutputPins[0];

					if (PinState.FirstBitHigh(enablePin.State)) outputPin.State = dataPin.State;
					else PinState.SetAllDisconnected(ref outputPin.State);

					break;
				}
				case ChipType.Key:
				{
					bool isHeld = SimKeyboardHelper.KeyIsHeld((char)chip.InternalState[0]);
					uint state = 0;
					PinState.SetTritValue(ref state, isHeld ? PinState.TritPositive : PinState.TritNegative);
					chip.OutputPins[0].State = state;
					break;
				}
				case ChipType.Rom_19683x9:
				{
					uint address = chip.InputPins[0].State;
					if (PinState.HasDisconnectedTrit(address, 9))
						PinState.SetAllDisconnected(ref chip.OutputPins[0].State);
					else
					{
						int index = PinState.GetTernaryDecimalValue(address, 9) + 9841;
						chip.OutputPins[0].State = chip.InternalState[index];
					}
					break;
				}
				// Legacy memory/display semantics are not defined for ternary yet.
				// Keep serialized data intact, but never index buffers with packed
				// ternary bits or inject binary bytes into a ternary signal.
				case ChipType.DisplayRGB:
				case ChipType.DisplayDot:
				case ChipType.dev_Ram_8Bit:
				case ChipType.Rom_256x16:
					foreach (SimPin output in chip.OutputPins) PinState.SetAllDisconnected(ref output.State);
					break;
				case ChipType.Buzzer:
					break; // Silent until ternary pitch/volume semantics are defined.
				// ---- Bus types ----
				default:
				{
					if (ChipTypeHelper.IsBusOriginType(chip.ChipType))
					{
						SimPin inputPin = chip.InputPins[0];
						PinState.Set(ref chip.OutputPins[0].State, inputPin.State);
					}

					break;
				}
			}
		}

		public static SimChip BuildSimChip(ChipDescription chipDesc, ChipLibrary library)
		{
			return BuildSimChip(chipDesc, library, -1, null);
		}

		public static SimChip BuildSimChip(ChipDescription chipDesc, ChipLibrary library, int subChipID, uint[] internalState)
		{
			SimChip simChip = BuildSimChipRecursive(chipDesc, library, subChipID, internalState);
			return simChip;
		}

		// Recursively build full representation of chip from its description for simulation.
		static SimChip BuildSimChipRecursive(ChipDescription chipDesc, ChipLibrary library, int subChipID, uint[] internalState)
		{
			// Recursively create subchips
			SimChip[] subchips = chipDesc.SubChips.Length == 0 ? Array.Empty<SimChip>() : new SimChip[chipDesc.SubChips.Length];

			for (int i = 0; i < chipDesc.SubChips.Length; i++)
			{
				SubChipDescription subchipDesc = chipDesc.SubChips[i];
				ChipDescription subchipFullDesc = library.GetChipDescription(subchipDesc.Name);
				SimChip subChip = BuildSimChipRecursive(subchipFullDesc, library, subchipDesc.ID, subchipDesc.InternalData);
				subchips[i] = subChip;
			}

			SimChip simChip = new(chipDesc, subChipID, internalState, subchips);


			// Create connections
			for (int i = 0; i < chipDesc.Wires.Length; i++)
			{
				simChip.AddConnection(chipDesc.Wires[i].SourcePinAddress, chipDesc.Wires[i].TargetPinAddress);
			}

			return simChip;
		}

		public static void AddPin(SimChip simChip, int pinID, bool isInputPin)
		{
			SimModifyCommand command = new()
			{
				type = SimModifyCommand.ModificationType.AddPin,
				modifyTarget = simChip,
				simPinToAdd = new SimPin(pinID, isInputPin, simChip),
				pinIsInputPin = isInputPin
			};
			modificationQueue.Enqueue(command);
		}

		public static void RemovePin(SimChip simChip, int pinID)
		{
			SimModifyCommand command = new()
			{
				type = SimModifyCommand.ModificationType.RemovePin,
				modifyTarget = simChip,
				removePinID = pinID
			};
			modificationQueue.Enqueue(command);
		}

		public static void AddSubChip(SimChip simChip, ChipDescription desc, ChipLibrary chipLibrary, int subChipID, uint[] subChipInternalData)
		{
			SimModifyCommand command = new()
			{
				type = SimModifyCommand.ModificationType.AddSubchip,
				modifyTarget = simChip,
				chipDesc = desc,
				lib = chipLibrary,
				subChipID = subChipID,
				subChipInternalData = subChipInternalData
			};
			modificationQueue.Enqueue(command);
		}

		public static void AddConnection(SimChip simChip, PinAddress source, PinAddress target)
		{
			SimModifyCommand command = new()
			{
				type = SimModifyCommand.ModificationType.AddConnection,
				modifyTarget = simChip,
				sourcePinAddress = source,
				targetPinAddress = target
			};
			modificationQueue.Enqueue(command);
		}

		public static void RemoveConnection(SimChip simChip, PinAddress source, PinAddress target)
		{
			SimModifyCommand command = new()
			{
				type = SimModifyCommand.ModificationType.RemoveConnection,
				modifyTarget = simChip,
				sourcePinAddress = source,
				targetPinAddress = target
			};
			modificationQueue.Enqueue(command);
		}

		public static void RemoveSubChip(SimChip simChip, int id)
		{
			SimModifyCommand command = new()
			{
				type = SimModifyCommand.ModificationType.RemoveSubChip,
				modifyTarget = simChip,
				removeSubChipID = id
			};
			modificationQueue.Enqueue(command);
		}

		// Note: this should only be called from the sim thread
		public static void ApplyModifications()
		{
			while (modificationQueue.Count > 0)
			{
				needsOrderPass = true;

				if (modificationQueue.TryDequeue(out SimModifyCommand cmd))
				{
					if (cmd.type == SimModifyCommand.ModificationType.AddSubchip)
					{
						SimChip newSubChip = BuildSimChip(cmd.chipDesc, cmd.lib, cmd.subChipID, cmd.subChipInternalData);
						cmd.modifyTarget.AddSubChip(newSubChip);
					}
					else if (cmd.type == SimModifyCommand.ModificationType.RemoveSubChip)
					{
						cmd.modifyTarget.RemoveSubChip(cmd.removeSubChipID);
					}
					else if (cmd.type == SimModifyCommand.ModificationType.AddConnection)
					{
						cmd.modifyTarget.AddConnection(cmd.sourcePinAddress, cmd.targetPinAddress);
					}
					else if (cmd.type == SimModifyCommand.ModificationType.RemoveConnection)
					{
						cmd.modifyTarget.RemoveConnection(cmd.sourcePinAddress, cmd.targetPinAddress); //
					}
					else if (cmd.type == SimModifyCommand.ModificationType.AddPin)
					{
						cmd.modifyTarget.AddPin(cmd.simPinToAdd, cmd.pinIsInputPin);
					}
					else if (cmd.type == SimModifyCommand.ModificationType.RemovePin)
					{
						cmd.modifyTarget.RemovePin(cmd.removePinID);
					}
				}
			}
		}

		public static void Reset()
		{
			simulationFrame = 0;
			modificationQueue?.Clear();
			stopwatch.Restart();
			elapsedSecondsOld = 0;
		}

		struct SimModifyCommand
		{
			public enum ModificationType
			{
				AddSubchip,
				RemoveSubChip,
				AddConnection,
				RemoveConnection,
				AddPin,
				RemovePin
			}

			public ModificationType type;
			public SimChip modifyTarget;
			public ChipDescription chipDesc;
			public ChipLibrary lib;
			public int subChipID;
			public uint[] subChipInternalData;
			public PinAddress sourcePinAddress;
			public PinAddress targetPinAddress;
			public SimPin simPinToAdd;
			public bool pinIsInputPin;
			public int removePinID;
			public int removeSubChipID;
		}
	}
}
