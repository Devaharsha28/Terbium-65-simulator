using System;
using System.IO;
using System.Linq;
using System.Reflection;
using DLS.Description;
using DLS.Simulation;
using DLS.Game;

static class TernaryValidation
{
	static int checks;
	static readonly Action<SimChip> Process = (Action<SimChip>)Delegate.CreateDelegate(typeof(Action<SimChip>), typeof(Simulator).GetMethod("ProcessBuiltinChip", BindingFlags.NonPublic | BindingFlags.Static));
	static void Check(bool condition, string message) { checks++; if (!condition) throw new Exception(message); }
	static uint Word(int n, int width) { uint state = 0; for (int i = 0; i < width; i++, n /= 3) PinState.SetTritAtIndex(ref state, i, (sbyte)(n % 3 - 1)); return state; }
	static PinDescription Pin(int id, int width) => new PinDescription { ID = id, Name = "P" + id, TritCount = (PinTritCount)width };
	static ChipDescription Desc(ChipType type, int ins, int outs, int width = 1) => new ChipDescription {
		Name = type.ToString(), ChipType = type, InputPins = Enumerable.Range(0,ins).Select(i => Pin(i,width)).ToArray(),
		OutputPins = Enumerable.Range(ins,outs).Select(i => Pin(i,width)).ToArray(),
		SubChips = Array.Empty<SubChipDescription>(), Wires = Array.Empty<WireDescription>() };
	static SimChip Chip(ChipType type, int ins, int outs) => new SimChip(Desc(type,ins,outs), 1, null, Array.Empty<SimChip>());
	static void Routing(ChipType splitType, ChipType mergeType, int parts, int width)
	{
		var split = Chip(splitType,1,parts); var merge = Chip(mergeType,parts,1);
		int total = (int)Math.Pow(3,width);
		for(int n=0;n<total;n++)
		{
			uint state=Word(n,width); PinState.Set(ref state,PinState.GetBitStates(state),(uint)n & ((1u<<width)-1));
			split.InputPins[0].State=state; Process(split);
			for(int i=0;i<parts;i++) merge.InputPins[i].State=split.OutputPins[i].State;
			Process(merge); Check(state==merge.OutputPins[0].State, "split/merge " + splitType);
		}
	}
	static int Main()
	{
		for(int n=0;n<19683;n++)
		{
			uint state=Word(n,9); Check(PinState.GetTernaryDecimalValue(state,9)==n-9841,"decimal");
			uint flagged=state; PinState.Set(ref flagged,PinState.GetBitStates(state),(uint)n & 511);
			Check(PinState.GetBitStates(flagged)==state,"logic preserved");
			Check(PinState.GetTristateFlags(flagged)==((uint)n & 511),"flags preserved");
			uint a=0,b=0,c=0,outState=0;
			PinState.Set3TritFrom9TritSource(ref a,flagged,0); PinState.Set3TritFrom9TritSource(ref b,flagged,1); PinState.Set3TritFrom9TritSource(ref c,flagged,2);
			PinState.Set9TritFrom3TritSources(ref outState,a,b,c); Check(flagged==outState,"packed roundtrip");
			foreach(int groupSize in new[]{2,3})
			{
				char[] buffer=new char[16]; int len=PinState.FormatGrouped(state,9,groupSize,buffer); uint restored=0;
				string formatted=new string(buffer,0,len);
				string[] tokens=groupSize==3 ? formatted.Split(' ') : formatted.Select(c=>c.ToString()).ToArray();
				for(int g=0;g<tokens.Length;g++)
				{
					string token=tokens[tokens.Length-1-g];
					int value=token[0]>='a' ? -(token[0]-'a'+1) : int.Parse(token);
					int encoded=value+(groupSize==2?4:13); // Decode balanced digits; not the display mapping.
					for(int i=0;i<groupSize;i++,encoded/=3) if(g*groupSize+i<9) PinState.SetTritAtIndex(ref restored,g*groupSize+i,(sbyte)(encoded%3-1));
				}
				Check(restored==state,"grouped reversible");
			}
		}
		Routing(ChipType.Split_3To1Trit,ChipType.Merge_1To3Trit,3,3);
		Routing(ChipType.Split_9To1Trit,ChipType.Merge_1To9Trit,9,9);
		Routing(ChipType.Split_9To3Trit,ChipType.Merge_3To9Trit,3,9);
		foreach(var type in new[]{ChipType.Not,ChipType.Min,ChipType.Max})
		{
			var gate=Chip(type,type==ChipType.Not?1:2,1);
			for(sbyte a=-1;a<=1;a++) for(sbyte b=-1;b<=1;b++)
			{
				PinState.SetTritValue(ref gate.InputPins[0].State,a);
				if(gate.InputPins.Length==2) PinState.SetTritValue(ref gate.InputPins[1].State,b);
				Process(gate); int expected=type==ChipType.Not?-a:type==ChipType.Min?Math.Min(a,b):Math.Max(a,b);
				Check(PinState.GetTritValue(gate.OutputPins[0].State)==expected && !PinState.IsTritDisconnected(gate.OutputPins[0].State),"gate " + type);
			}
			PinState.SetAllDisconnected(ref gate.InputPins[0].State); Process(gate); Check(PinState.IsTritDisconnected(gate.OutputPins[0].State),"gate floating");
		}
		foreach(int width in new[]{1,3,9})
		{
			var bus=Chip(width==1?ChipType.Bus_1Trit:width==3?ChipType.Bus_3Trit:ChipType.Bus_9Trit,1,1);
			var target=new SimPin(99,true,new SimChip()); bus.OutputPins[0].ConnectedTargetPins=new[]{target};
			for(int flags=0;flags<(1<<width);flags++)
			{
				uint state=Word(12345,width); PinState.Set(ref state,PinState.GetBitStates(state),(uint)flags);
				bus.InputPins[0].State=state; Process(bus); Simulator.simulationFrame++; bus.OutputPins[0].PropagateSignal();
				Check(target.State==state,"bus propagation");
			}
			for(int i=0;i<width;i++)
			{
				uint state=Word(0,width); for(int turn=0;turn<3;turn++) {
					PinState.Toggle(ref state,i); Check(PinState.GetTritAtIndex(state,i)==new[]{0,1,-1}[turn],"cycle");
					for(int other=0;other<width;other++) if(other!=i) Check(PinState.GetTritAtIndex(state,other)==-1,"other cells unchanged");
				}
				Check(state==Word(0,width),"only target changed");
			}
		}
		var tri=Chip(ChipType.TriStateBuffer,2,1);
		for(sbyte enable=-1;enable<=1;enable++) for(sbyte data=-1;data<=1;data++)
		{
			PinState.SetTritValue(ref tri.InputPins[0].State,data); PinState.SetTritValue(ref tri.InputPins[1].State,enable); Process(tri);
			Check(enable==1 ? tri.OutputPins[0].State==tri.InputPins[0].State : PinState.IsTritDisconnected(tri.OutputPins[0].State),"tristate");
		}
		var source=new SimPin(1,false,new SimChip()); var floating=new SimPin(2,false,new SimChip()); var dest=new SimPin(3,true,new SimChip());
		source.State=Word(9841,9); source.ConnectedTargetPins=floating.ConnectedTargetPins=new[]{dest};
		Simulator.simulationFrame++; source.PropagateSignal(); floating.PropagateSignal(); Check(dest.State==source.State,"floating cannot erase driven zero");
		foreach(var type in new[]{ChipType.Rom_256x16,ChipType.dev_Ram_8Bit,ChipType.DisplayRGB,ChipType.DisplayDot})
		{
			var legacy=Chip(type,8,3); foreach(var pin in legacy.InputPins) pin.State=uint.MaxValue; Process(legacy);
			Check(legacy.OutputPins.All(p=>PinState.GetTristateFlags(p.State)==511),"legacy isolated");
		}
		var nand=Chip(ChipType.Nand,2,1);
		for(sbyte a=-1;a<=1;a++) for(sbyte b=-1;b<=1;b++) {
			PinState.SetTritValue(ref nand.InputPins[0].State,a); PinState.SetTritValue(ref nand.InputPins[1].State,b); Process(nand);
			Check(!PinState.IsTritDisconnected(nand.OutputPins[0].State) && PinState.GetTritValue(nand.OutputPins[0].State)==-Math.Min(a,b),"ternary NAND");
		}
		Console.WriteLine("PASS: " + checks + " simulation/state assertions");
		Persistence();
		Layout();
		FeatureCompletion();
		Console.WriteLine("TOTAL: " + checks + " passed, 0 failed");
		return 0;
	}
	static string Grouped(uint state, int width, int size) { var chars=new char[16]; return new string(chars,0,PinState.FormatGrouped(state,width,size,chars)); }
	static void FeatureCompletion()
	{
		int start=checks;
		var unary = new (ChipType type, int[] table)[] {
			(ChipType.Buf,new[]{-1,0,1}), (ChipType.Not,new[]{1,0,-1}),
			(ChipType.PNot,new[]{1,1,-1}), (ChipType.NNot,new[]{1,-1,-1}),
			(ChipType.Abs,new[]{1,0,1}), (ChipType.Clu,new[]{0,0,1}), (ChipType.Cld,new[]{-1,0,0}),
			(ChipType.Inc,new[]{0,1,-1}), (ChipType.Dec,new[]{1,-1,0}),
			(ChipType.Rtu,new[]{0,1,-1}), (ChipType.Rtd,new[]{1,-1,0}),
			(ChipType.Isp,new[]{-1,-1,1}), (ChipType.Isz,new[]{-1,1,-1}), (ChipType.Isn,new[]{1,-1,-1})
		};
		var binary = new (ChipType type, int[] table)[] {
			(ChipType.And,new[]{-1,-1,-1,-1,0,0,-1,0,1}), (ChipType.Min,new[]{-1,-1,-1,-1,0,0,-1,0,1}),
			(ChipType.Nand,new[]{1,1,1,1,0,0,1,0,-1}),
			(ChipType.Or,new[]{-1,0,1,0,0,1,1,1,1}), (ChipType.Max,new[]{-1,0,1,0,0,1,1,1,1}),
			(ChipType.Nor,new[]{1,0,-1,0,0,-1,-1,-1,-1}),
			(ChipType.Cons,new[]{-1,0,0,0,0,0,0,0,1}), (ChipType.NCons,new[]{1,0,0,0,0,0,0,0,-1}),
			(ChipType.Any,new[]{-1,0,1,0,0,1,1,1,1}), (ChipType.NAny,new[]{1,0,-1,0,0,-1,-1,-1,-1}),
			(ChipType.Mul,new[]{1,0,-1,0,0,0,-1,0,1}), (ChipType.NMul,new[]{-1,0,1,0,0,0,1,0,-1}),
			(ChipType.Sum,new[]{1,-1,0,-1,0,1,0,1,-1}), (ChipType.NSum,new[]{-1,1,0,1,0,-1,0,-1,1})
		};
		foreach(var entry in unary) {
			var gate=Chip(entry.type,1,1);
			for(int a=-1;a<=1;a++) { PinState.SetTritValue(ref gate.InputPins[0].State,(sbyte)a); Process(gate);
				Check(!PinState.IsTritDisconnected(gate.OutputPins[0].State) && PinState.GetTritValue(gate.OutputPins[0].State)==entry.table[a+1],"unary "+entry.type); }
			PinState.SetAllDisconnected(ref gate.InputPins[0].State); Process(gate); Check(PinState.IsTritDisconnected(gate.OutputPins[0].State),"unary floating");
		}
		foreach(var entry in binary) {
			var gate=Chip(entry.type,2,1);
			for(int a=-1;a<=1;a++) for(int b=-1;b<=1;b++) {
				PinState.SetTritValue(ref gate.InputPins[0].State,(sbyte)a); PinState.SetTritValue(ref gate.InputPins[1].State,(sbyte)b); Process(gate);
				Check(!PinState.IsTritDisconnected(gate.OutputPins[0].State) && PinState.GetTritValue(gate.OutputPins[0].State)==entry.table[(a+1)*3+b+1],"binary "+entry.type);
			}
			for(int input=0;input<2;input++) {
				foreach(var pin in gate.InputPins) PinState.SetTritValue(ref pin.State,0);
				PinState.SetAllDisconnected(ref gate.InputPins[input].State); Process(gate);
				Check(PinState.IsTritDisconnected(gate.OutputPins[0].State),"binary floating");
			}
		}
		Console.WriteLine("PASS: gate tables and disconnected propagation: "+(checks-start)+" assertions (14 unary, 14 binary including MIN/MAX)");
		start=checks;
		string[] nonary={"d","c","b","a","0","1","2","3","4"};
		string[] hept={"m","l","k","j","i","h","g","f","e","d","c","b","a","0","1","2","3","4","5","6","7","8","9","10","11","12","13"};
		for(int n=0;n<9;n++) Check(Grouped(Word(n,2),2,2)==nonary[n],"nonary symbol");
		for(int n=0;n<27;n++) Check(Grouped(Word(n,3),3,3)==hept[n],"hept token");
		Check(Grouped(PinState.FromDecimal9(9841),9,3)=="13 13 13","hept separators");
		Check(Grouped(PinState.FromDecimal9(-9841),9,3)=="m m m","hept negative");
		Check(Grouped(PinState.FromDecimal9(9841),9,2)=="14444","odd nonary group");
		Check(Grouped(PinState.FromDecimal9(-9841),9,2)=="adddd","negative odd group");
		foreach(int width in new[]{1,3,9}) foreach(int size in new[]{2,3}) for(int index=0;index<width;index++) {
			uint floating=PinState.FromDecimal9(0); PinState.SetTritAtIndexDisconnected(ref floating,index);
			Check(Grouped(floating,width,size).Contains("?"),"floating group");
		}
		Console.WriteLine("PASS: notation symbols, padding and floating groups: "+(checks-start)+" assertions");
		start=checks;
		var clock=Chip(ChipType.Clock,0,1); Simulator.stepsPerClockTransition=2;
		foreach(int frame in new[]{2,4,6}) { Simulator.simulationFrame=frame; Process(clock);
			Check(PinState.GetTritValue(clock.OutputPins[0].State)==(frame==4?1:0) && !PinState.IsTritDisconnected(clock.OutputPins[0].State),"clock 0/1/0"); }
		Simulator.stepsPerClockTransition=0; Process(clock); Check(PinState.GetTritValue(clock.OutputPins[0].State)==0,"clock disabled zero");
		var pulse=new SimChip(Desc(ChipType.Pulse,1,1),1,new uint[]{2,0,0},Array.Empty<SimChip>());
		foreach(var step in new[]{(input:0,output:0),(input:1,output:1),(input:1,output:1),(input:1,output:0)}) {
			PinState.SetTritValue(ref pulse.InputPins[0].State,(sbyte)step.input);
			Process(pulse); Check(!PinState.IsTritDisconnected(pulse.OutputPins[0].State) && PinState.GetTritValue(pulse.OutputPins[0].State)==step.output,"pulse sequence");
		}
		PinState.SetAllDisconnected(ref pulse.InputPins[0].State); Process(pulse); Check(PinState.IsTritDisconnected(pulse.OutputPins[0].State),"pulse floating");
		Console.WriteLine("PASS: clock/pulse: "+(checks-start)+" assertions");
		start=checks;
		var rom=new SimChip(Desc(ChipType.Rom_19683x9,1,1,9),1,null,Array.Empty<SimChip>());
		Check(rom.InternalState.Length==19683 && rom.InternalState.All(w=>PinState.GetTernaryDecimalValue(w,9)==0),"ROM zero-filled");
		for(int n=0;n<19683;n++) rom.InternalState[n]=Word(19682-n,9);
		for(int n=0;n<19683;n++) {
			rom.InputPins[0].State=PinState.FromDecimal9(n-9841); Process(rom);
			Check(rom.OutputPins[0].State==Word(19682-n,9),"ROM signed address and word");
		}
		foreach(int address in new[]{-9841,0,9841}) {
			rom.InputPins[0].State=PinState.FromDecimal9(address); Process(rom);
			Check(rom.OutputPins[0].State==rom.InternalState[address+9841],"ROM boundary "+address);
		}
		for(int i=0;i<9;i++) { rom.InputPins[0].State=PinState.FromDecimal9(0); PinState.SetTritAtIndexDisconnected(ref rom.InputPins[0].State,i); Process(rom);
			Check(PinState.GetTristateFlags(rom.OutputPins[0].State)==511,"ROM floating address"); }
		var container=Desc(ChipType.Custom,0,0); container.SubChips=new[]{new SubChipDescription {Name=ChipTypeHelper.GetName(ChipType.Rom_19683x9),ID=1,InternalData=rom.InternalState}};
		var saved=Serializer.DeserializeChipDescription(Serializer.SerializeChipDescription(container));
		var reopened=new SimChip(Desc(ChipType.Rom_19683x9,1,1,9),1,saved.SubChips[0].InternalData,Array.Empty<SimChip>());
		Check(reopened.InternalState.SequenceEqual(rom.InternalState),"ROM persistence all words");
		Check(new SimChip(Desc(ChipType.Rom_19683x9,1,1,9),1,new uint[]{PinState.FromDecimal9(1)},Array.Empty<SimChip>()).InternalState.Length==19683,"ROM short data normalized");
		Console.WriteLine("PASS: ROM addressing/data/persistence: "+(checks-start)+" assertions");
		start=checks;
		var builtins=BuiltinChipCreator.CreateAllBuiltinChipDescriptions();
		Check(builtins.Select(d=>d.Name).Distinct().Count()==builtins.Length,"unique builtin names");
		Check(builtins.Select(d=>d.ChipType).Distinct().Count()==builtins.Length,"unique builtin types");
		foreach(var entry in unary) { var desc=builtins.Single(d=>d.ChipType==entry.type); Check(desc.InputPins.Length==1 && desc.OutputPins.Length==1,"unary descriptor"); }
		foreach(var entry in binary) { var desc=builtins.Single(d=>d.ChipType==entry.type); Check(desc.InputPins.Length==2 && desc.OutputPins.Length==1,"binary descriptor"); }
		var native=builtins.Single(d=>d.ChipType==ChipType.Rom_19683x9);
		Check(native.InputPins.Single().TritCount==PinTritCount.Trit9 && native.OutputPins.Single().TritCount==PinTritCount.Trit9,"ROM descriptor");
		Check(builtins.Any(d=>d.ChipType==ChipType.Rom_256x16),"legacy ROM available");
		foreach(var desc in builtins) Check(desc.InputPins.Concat(desc.OutputPins).All(p=>p.TritCount is PinTritCount.Trit1 or PinTritCount.Trit3 or PinTritCount.Trit9),"valid builtin widths");
		Check(DLS.SaveSystem.DescriptionCreator.CreateDefaultInstanceData(ChipType.Rom_19683x9).SequenceEqual(PinState.CreateRom9Data()),"editor ROM defaults");
		Console.WriteLine("PASS: builtin library structure: "+(checks-start)+" assertions");
	}
	static void Layout()
	{
		foreach(int width in new[]{1,3,9}) {
			var input=new DevPinInstance(Pin(0,width),true);
			var output=new DevPinInstance(Pin(1,width),false);
			Check(input.StateGridDimensions.x*input.StateGridDimensions.y==width,"cell count");
			if(width==9) Check(input.StateGridDimensions.x==3 && input.StateGridDimensions.y==3,"3x3 grid");
			var visited=new System.Collections.Generic.HashSet<int>();
			var centres=new System.Collections.Generic.HashSet<UnityEngine.Vector2>();
			for(int row=0;row<input.StateGridDimensions.y;row++) for(int col=0;col<input.StateGridDimensions.x;col++) {
				int index=input.GetCellTritIndex(col,row); Check(visited.Add(index),"unique cell");
				var centre=input.GetCellCentre(col,row);
				Check(centres.Add(centre),"unique cell centre");
				Check(input.PointIsInStateIndicatorBounds(centre),"cell inside hit bounds");
				Check(output.GetCellTritIndex(col,row)==index,"input output mapping");
				uint before=input.Pin.PlayerInputState;
				input.ToggleState(index);
				for(int i=0;i<width;i++) Check(PinState.GetTritAtIndex(input.Pin.PlayerInputState,i)==(i==index?0:PinState.GetTritAtIndex(before,i)),"cell input isolation");
				uint outBefore=output.Pin.PlayerInputState; output.ToggleState(index); Check(output.Pin.PlayerInputState==outBefore,"output read only");
			}
		}
		Console.WriteLine("PASS: 1/3/9 cell layout, shared index mapping, isolated input changes, read-only outputs");
	}
	static void Persistence()
	{
		var desc=Desc(ChipType.Custom,3,3); desc.Name="TernaryValidation"; desc.DLSVersion="2.1.6";
		for(int i=0;i<3;i++) { desc.InputPins[i].TritCount=(PinTritCount)new[]{1,3,9}[i]; desc.OutputPins[i].TritCount=desc.InputPins[i].TritCount; }
		desc.SubChips=new[]{new SubChipDescription {Name="NOT",ID=7,InternalData=new uint[]{0x7FFFFFF}}};
		desc.Wires=new[]{new WireDescription {SourcePinAddress=new PinAddress(0,0),TargetPinAddress=new PinAddress(3,0),Points=Array.Empty<UnityEngine.Vector2>()}};
		string json=Serializer.SerializeChipDescription(desc); string path=Path.Combine(AppContext.BaseDirectory,"roundtrip.json"); File.WriteAllText(path,json);
		var restored=Serializer.DeserializeChipDescription(File.ReadAllText(path));
		Check(restored.InputPins.Select(p=>(int)p.TritCount).SequenceEqual(new[]{1,3,9}),"width persistence");
		Check(restored.SubChips[0].InternalData[0]==0x7FFFFFF && restored.Wires.Length==1,"hierarchy persistence");
		Check(!json.Contains("BitCount"),"canonical property");
		var old=Serializer.DeserializeChipDescription(json.Replace("TritCount","BitCount")); Check(old.InputPins[2].TritCount==PinTritCount.Trit9,"old property compatibility");
		bool rejected=false;
		try { Serializer.DeserializeChipDescription(System.Text.RegularExpressions.Regex.Replace(json,"\"TritCount\":\\s*9","\"TritCount\":8")); } catch(NotSupportedException) { rejected=true; }
		Check(rejected,"legacy binary width must not silently migrate");
		Console.WriteLine("PASS: persistence roundtrip with 1/3/9 widths, hierarchy, wires and uint data");
	}
}
