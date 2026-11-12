using System;
using System.Linq;
using DLS.Description;
using DLS.Game;
using DLS.Graphics;
using DLS.SaveSystem;
using DLS.Simulation;
using UnityEngine;

static class UIMergeValidation
{
    static int count;
    static void Check(bool ok, string label) { count++; if (!ok) throw new Exception(label); }
    static void Main()
    {
        foreach (int value in new[] {-9841,-9840,-729,-13,-4,-1,0,1,4,13,729,9840,9841})
        {
            uint original = PinState.FromDecimal9(value), word = original;
            foreach (TernaryRomText.Mode mode in Enum.GetValues(typeof(TernaryRomText.Mode)))
            {
                string text = TernaryRomText.Format(word, mode);
                Check(TernaryRomText.TryParse(text, mode, out word) && word == original, "ROM mode roundtrip");
            }
        }
        Check(TernaryRomText.Format(PinState.FromDecimal9(-9841), TernaryRomText.Mode.Nonary) == "adddd", "nonary unchanged");
        Check(TernaryRomText.Format(PinState.FromDecimal9(9841), TernaryRomText.Mode.Hept) == "13 13 13", "Hept unchanged");
        foreach (var item in new[] {
            (TernaryRomText.Mode.Decimal,"9842"), (TernaryRomText.Mode.Decimal,"-9842"),
            (TernaryRomText.Mode.Decimal,"999999999999999999999"),
            (TernaryRomText.Mode.Ternary,"--------"), (TernaryRomText.Mode.Ternary,"000000002"),
            (TernaryRomText.Mode.Nonary,"ddddd"), (TernaryRomText.Mode.Nonary,"24444"),
            (TernaryRomText.Mode.Nonary,"1ddd5"), (TernaryRomText.Mode.Hept,"13 14 0"),
            (TernaryRomText.Mode.Hept,"13 0"), (TernaryRomText.Mode.Hept,"01 0 0"),
            (TernaryRomText.Mode.Hept,"n 0 0"), (TernaryRomText.Mode.Decimal,"") })
            Check(!TernaryRomText.TryParse(item.Item2,item.Item1,out _), "invalid ROM rejected");
        Check(EditorWorkspace.HeaderText(Color.white) == Color.black, "light header contrast");
        Check(EditorWorkspace.HeaderText(Color.black) == Color.white, "dark header contrast");
        Check(EditorWorkspace.HeaderText(new Color(1,1,0)) == Color.black, "yellow header contrast");
        Check(EditorWorkspace.HeaderColor(null) == EditorWorkspace.HeaderColor("#484848"), "old save default");
        var pinDesc = new PinDescription("IN",1,Vector2.zero,PinTritCount.Trit1,PinColour.White,PinValueDisplayMode.Ternary,"#AACCEE");
        var devPin = new DevPinInstance(pinDesc,true);
        Check(DescriptionCreator.CreatePinDescription(devPin).HeaderColorHex == "#AACCEE","pin appearance serialized");
        var circuit = new ChipDescription {
            Name="appearance-test", ChipType=ChipType.Custom,
            InputPins=new[]{pinDesc}, OutputPins=Array.Empty<PinDescription>(),
            SubChips=new[]{
                new SubChipDescription("NOT",2,"first",Vector2.zero,Array.Empty<OutputPinColourInfo>(),null,"#112233"),
                new SubChipDescription("NOT",3,"second",Vector2.one,Array.Empty<OutputPinColourInfo>(),null,"#FFEEDD")},
            Wires=Array.Empty<WireDescription>()
        };
        var restored = Serializer.DeserializeChipDescription(Serializer.SerializeChipDescription(circuit));
        Check(restored.SubChips[0].HeaderColorHex=="#112233" && restored.SubChips[1].HeaderColorHex=="#FFEEDD","per-instance identity colors");
        Check(restored.InputPins[0].HeaderColorHex=="#AACCEE","input appearance roundtrip");
        circuit.SubChips[0].HeaderColorHex = null;
        restored=Serializer.DeserializeChipDescription(Serializer.SerializeChipDescription(circuit));
        Check(restored.SubChips[0].HeaderColorHex==null,"legacy null metadata");
        var graph = new DevChipInstance();
        graph.Elements.Add(devPin);
        uint stateBefore=devPin.Pin.PlayerInputState;
        graph.UndoController.RecordAppearance(devPin,"#AACCEE","#112233");
        devPin.HeaderColorHex="#112233";
        graph.UndoController.TryUndo();
        Check(devPin.HeaderColorHex=="#AACCEE","appearance undo");
        graph.UndoController.TryRedo();
        Check(devPin.HeaderColorHex=="#112233","appearance redo");
        graph.UndoController.RecordAppearance(devPin,"#112233",null); devPin.HeaderColorHex=null;
        graph.UndoController.TryUndo();
        Check(devPin.HeaderColorHex=="#112233","reset undo");
        Check(devPin.Pin.PlayerInputState==stateBefore,"appearance never changes signals");
        for (int i=0;i<3;i++) { devPin.ToggleState(0); Check(PinState.GetTritValue(devPin.Pin.PlayerInputState)==new[]{0,1,-1}[i],"graph input cycle"); }
        foreach(int width in new[]{1,3,9})
        {
            pinDesc.TritCount=(PinTritCount)width;
            var pin=new DevPinInstance(pinDesc,true);
            Check(pin.StateGridDimensions.x*pin.StateGridDimensions.y==width,"cell count retained");
        }
        Console.WriteLine("PASS: "+count+" focused ROM/UI/appearance assertions; 0 failed");
    }
}

