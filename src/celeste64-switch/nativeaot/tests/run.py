"""Run a host NativeAOT check of the exact generated SharpGLTF adaptation."""
from pathlib import Path
import subprocess, sys
from xml.sax.saxutils import quoteattr
here=Path(__file__).resolve().parent
root=here.parents[3]
out=root/'artifacts/celeste64-nativeaot-model-tests'
core=root/'artifacts/celeste64-nativeaot-managed/managed/SharpGLTF.Core/SharpGLTF.Core.csproj'
if not core.is_file():raise SystemExit('Run nativeaot/build-managed.sh first')
models=Path(sys.argv[1]) if len(sys.argv)>1 else root/'artifacts/celeste64-switch-v120-bootstrap/romfs/Content/Models'
if not models.is_dir():raise SystemExit('Model directory missing')
out.mkdir(parents=True,exist_ok=True)
project=out/'Models.csproj'
project.write_text(f'''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>
<TargetFramework>net9.0</TargetFramework><OutputType>Exe</OutputType>
<ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><PublishAot>true</PublishAot>
<RuntimeFrameworkVersion>9.0.3</RuntimeFrameworkVersion><IlcPackageVersion>9.0.3</IlcPackageVersion>
</PropertyGroup><ItemGroup><Compile Include={quoteattr(str(here/'Models.cs'))}/>
<ProjectReference Include={quoteattr(str(core))}/></ItemGroup></Project>''')
with (out/'build.log').open('w') as log:
    subprocess.run(['dotnet','publish',str(project),'-c','Release','-r','linux-x64'],stdout=log,stderr=subprocess.STDOUT,check=True)
with (out/'results.txt').open('w') as log:
    subprocess.run([str(out/'bin/Release/net9.0/linux-x64/publish/Models'),str(models)],stdout=log,stderr=subprocess.STDOUT,check=True)
print((out/'results.txt').read_text(),end='')
