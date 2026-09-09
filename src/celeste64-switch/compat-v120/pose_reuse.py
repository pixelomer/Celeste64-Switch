"""Retain drawable preparation until any node in its armature changes."""

def optimize_pose_reuse(out, replace):
    p = out / 'managed/SharpGLTF/ArmatureInstance.cs'
    s = p.read_text()
    s = replace(s, 'public class ArmatureInstance\n    {', 'public class ArmatureInstance\n    {\n        // Saturation disables reuse permanently; no generation can alias.\n        public ulong PoseRevision { get; private set; } = 1;\n        internal void MarkPoseChanged() { if(PoseRevision < ulong.MaxValue) PoseRevision++; }')
    s = replace(s, 'new NodeInstance(n, p)', 'new NodeInstance(n, p, this)')
    p.write_text(s)
    p = out / 'managed/SharpGLTF/NodeInstance.cs'
    s = p.read_text()
    s = replace(s, 'NodeInstance(NodeTemplate template, NodeInstance parent)', 'NodeInstance(NodeTemplate template, NodeInstance parent, ArmatureInstance owner)')
    s = replace(s, '_Template = template;', '_Owner = owner;\n            _Template = template;')
    s = replace(s, 'private readonly NodeTemplate _Template;', 'private readonly ArmatureInstance _Owner;\n        private readonly NodeTemplate _Template;')
    s = replace(s, 'set => _MorphWeights = value;', 'set { _MorphWeights = value; _Owner.MarkPoseChanged(); }')
    s = replace(s, '_LocalMatrix = value;', '_LocalMatrix = value;\n                _Owner.MarkPoseChanged();')
    p.write_text(s)
    p = out / 'managed/Game/DrawableFrameCache.cs'
    s = p.read_text()
    p.write_text(s)
