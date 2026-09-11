using System.Numerics;
using System.Text;
using System.Text.Json.Nodes;
using SharpGLTF.Schema2;
using SharpGLTF.Validation;

static byte[] Glb(string json)
{
    byte[] bytes=Encoding.UTF8.GetBytes(json);
    int length=(bytes.Length+3)&~3;
    using var stream=new MemoryStream();using var writer=new BinaryWriter(stream);
    writer.Write(0x46546c67);writer.Write(2);writer.Write(20+length);
    writer.Write(length);writer.Write(0x4e4f534a);writer.Write(bytes);
    for(int i=bytes.Length;i<length;i++)writer.Write((byte)' ');
    return stream.ToArray();
}
static void Check(bool condition,string reason) { if(!condition)throw new Exception(reason); }

const string json="""
{"asset":{"version":"2.0"},"extensionsUsed":["TEST_unknown"],"nodes":[{"name":"probe","extras":{"text":"héllo","array":[1,true,null,{"nested":2}]},"extensions":{"TEST_unknown":{"array":[3,false,{"value":"kept"}]}}}]}
""";
var model=ModelRoot.ParseGLB(Glb(json));
var expected=JsonNode.Parse(json)!;
var serialized=JsonNode.Parse(model.GetJsonPreview())!;
Check(JsonNode.DeepEquals(expected["nodes"]![0]!["extensions"],serialized["nodes"]![0]!["extensions"]),"unknown extension changed");
Check(JsonNode.DeepEquals(expected["nodes"]![0]!["extras"],serialized["nodes"]![0]!["extras"]),"extras changed");
var input=JsonNode.Parse("""{"nested":{"value":7}}""")!;
model.LogicalNodes[0].Extras=input;
input["nested"]!["value"]=99;
Check(model.LogicalNodes[0].Extras!["nested"]!["value"]!.GetValue<int>()==7,"extras setter did not deep clone");
try {
    ModelRoot.ParseGLB(Glb("""{"asset":{"version":"2.0"},"nodes":[{"mesh":99}]}"""));
    throw new Exception("invalid reference accepted");
} catch(ModelException e) {
    Check(e.Message.Contains("Node[0]"),"diagnostic lost node index: "+e.Message);
    Console.WriteLine("diagnostic_index=PASS");
}
Console.WriteLine("json_dom_roundtrip=PASS");
int count=0,nodes=0,meshes=0,animations=0;
foreach(string path in Directory.GetFiles(args[0],"*.glb",SearchOption.AllDirectories).Order()) {
    var source=ModelRoot.Load(path);
    var copy=ModelRoot.ParseGLB(source.WriteGLB());
    Check(source.LogicalNodes.Count==copy.LogicalNodes.Count && source.LogicalMeshes.Count==copy.LogicalMeshes.Count && source.LogicalAnimations.Count==copy.LogicalAnimations.Count,"model roundtrip counts changed: "+Path.GetFileName(path));
    nodes+=source.LogicalNodes.Count;meshes+=source.LogicalMeshes.Count;animations+=source.LogicalAnimations.Count;count++;
}
Check(count>0,"no model inputs");
Console.WriteLine($"models_roundtrip=PASS files={count} nodes={nodes} meshes={meshes} animations={animations}");
