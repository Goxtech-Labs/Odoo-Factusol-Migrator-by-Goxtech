from . import tools
from . import models
from . import wizard


def post_init_seed(env):
    """Seed the table/field catalog and the factory presets from the schema."""
    env["factusol.table.profile"]._seed_from_catalog()
    env["factusol.import.profile"]._seed_presets()
