"""Use the known int-backed flags directly in World render filtering."""

def optimize_modelbits(override):
    override('Scenes/World.cs', [('!it.Model.Flags.Has(flags)', '(it.Model.Flags & flags) == 0'), ('it.Model.Flags.Has(ModelFlags.StrawberryGetEffect)', '(it.Model.Flags & ModelFlags.StrawberryGetEffect) != 0')])
