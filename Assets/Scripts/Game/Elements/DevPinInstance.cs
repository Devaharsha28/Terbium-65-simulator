using System;
using DLS.Description;
using DLS.Simulation;
using Seb.Helpers;
using Seb.Types;
using UnityEngine;
using static DLS.Graphics.DrawSettings;

namespace DLS.Game
{
	public class DevPinInstance : IMoveable
	{
		public readonly PinTritCount BitCount;
		public readonly char[] decimalDisplayCharBuffer = new char[16];

		// Size/Layout info
		public readonly Vector2 faceDir;

		public readonly bool IsInputPin;
		public readonly string Name;
		public readonly PinInstance Pin;
		public readonly Vector2Int StateGridDimensions;
		public readonly Vector2 StateGridSize;

		public PinValueDisplayMode pinValueDisplayMode;

		public DevPinInstance(PinDescription pinDescription, bool isInput)
		{
			Name = pinDescription.Name;
			ID = pinDescription.ID;
			IsInputPin = isInput;
			Position = pinDescription.Position;
			BitCount = pinDescription.TritCount;

			Pin = new PinInstance(pinDescription, new PinAddress(ID, 0), this, isInput);
			pinValueDisplayMode = pinDescription.ValueDisplayMode;

			// Initialize ternary state for all input pins
			if (IsInputPin)
			{
				PinState.Set(ref Pin.PlayerInputState, 0, 0); 
			}

			// Calculate layout info
			faceDir = new Vector2(IsInputPin ? 1 : -1, 0);
			StateGridDimensions = BitCount switch
			{
				PinTritCount.Trit1 => new Vector2Int(1, 1),
				PinTritCount.Trit3 => new Vector2Int(1, 3),
				PinTritCount.Trit9 => new Vector2Int(3, 3),
				_ => throw new Exception("Bit count not implemented")
			};
			StateGridSize = BitCount switch
			{
				PinTritCount.Trit1 => Vector2.one * (DevPinStateDisplayRadius * 2 + DevPinStateDisplayOutline * 2),
				_ => (Vector2)StateGridDimensions * MultiBitPinStateDisplaySquareSize + Vector2.one * DevPinStateDisplayOutline
			};
		}

		public Vector2 HandlePosition => Position;
		public Vector2 StateDisplayPosition => HandlePosition + faceDir * (DevPinHandleWidth / 2 + StateGridSize.x / 2 + 0.065f);

		public Vector2 PinPosition
		{
			get
			{
				int gridDst = BitCount is PinTritCount.Trit1 or PinTritCount.Trit3 ? 6 : 9;
				return HandlePosition + faceDir * (GridSize * gridDst);
			}
		}


		public Vector2 Position { get; set; }
		public Vector2 MoveStartPosition { get; set; }
		public Vector2 StraightLineReferencePoint { get; set; }
		public int ID { get; }

		public bool IsSelected { get; set; }
		public bool HasReferencePointForStraightLineMovement { get; set; }
		public bool IsValidMovePos { get; set; }

		public Bounds2D SelectionBoundingBox => CreateBoundingBox(SelectionBoundsPadding);

		public Bounds2D BoundingBox => CreateBoundingBox(0);


		public Vector2 SnapPoint => Pin.GetWorldPos();

		public bool ShouldBeIncludedInSelectionBox(Vector2 selectionCentre, Vector2 selectionSize)
		{
			Bounds2D selfBounds = SelectionBoundingBox;
			return Maths.BoxesOverlap(selectionCentre, selectionSize, selfBounds.Centre, selfBounds.Size);
		}

		public int GetStateDecimalDisplayValue()
		{
			uint state = DisplayState;
			int numTrits = BitCount switch
			{
				PinTritCount.Trit1 => 1,
				PinTritCount.Trit3 => 3,
				PinTritCount.Trit9 => 9,
				_ => 1
			};
			return PinState.GetTernaryDecimalValue(state, numTrits);
		}

		public uint DisplayState => IsInputPin && Project.ActiveProject.CanEditViewedChip ? Pin.PlayerInputState : Pin.State;

		public int CreateTernaryString(char[] buffer) => PinState.FormatTernary(DisplayState, (int)BitCount, buffer);
		public int CreateGroupedString(char[] buffer, int groupSize) => PinState.FormatGrouped(DisplayState, (int)BitCount, groupSize, buffer);

		// MSB at top left; rendering and hit-testing share these exact positions.
		public int GetCellTritIndex(int column, int row) => (int)BitCount - 1 - (row * StateGridDimensions.x + column);
		public Vector2 GetCellCentre(int column, int row)
		{
			Vector2 size = (Vector2)StateGridDimensions * MultiBitPinStateDisplaySquareSize;
			return StateDisplayPosition + new Vector2(-size.x / 2, size.y / 2) +
				MultiBitPinStateDisplaySquareSize * new Vector2(column + 0.5f, -row - 0.5f);
		}

		Bounds2D CreateBoundingBox(float pad)
		{
			float x1 = HandlePosition.x - faceDir.x * DevPinHandleWidth / 2;
			float x2 = PinPosition.x + faceDir.x * PinRadius;
			float minX = Mathf.Min(x1, x2);
			float maxX = Mathf.Max(x1, x2);

			Vector2 centre = new((minX + maxX) / 2, HandlePosition.y);
			Vector2 size = new Vector2(maxX - minX, BoundsHeight()) + Vector2.one * pad;
			return Bounds2D.CreateFromCentreAndSize(centre, size);
		}

		public Bounds2D HandleBounds() => Bounds2D.CreateFromCentreAndSize(HandlePosition, GetHandleSize());

		public float BoundsHeight() => StateGridSize.y;

		public Vector2 GetHandleSize() => new(DevPinHandleWidth, BoundsHeight());

		public void ToggleState(int bitIndex)
		{
			if (IsInputPin && bitIndex >= 0 && bitIndex < (int)BitCount)
			{
				PinState.Toggle(ref Pin.PlayerInputState, bitIndex);
			}
		}

		public bool PointIsInInteractionBounds(Vector2 point) => PointIsInHandleBounds(point) || PointIsInStateIndicatorBounds(point);

		public bool PointIsInStateIndicatorBounds(Vector2 point) => BitCount == PinTritCount.Trit1
			? Maths.PointInCircle2D(point, StateDisplayPosition, DevPinStateDisplayRadius)
			: Bounds2D.CreateFromCentreAndSize(StateDisplayPosition, StateGridSize).PointInBounds(point);

		public bool PointIsInHandleBounds(Vector2 point) => HandleBounds().PointInBounds(point);
	}
}
