"""tests for dispute logic of auto-disputer"""

import pytest
from tellor_disputables.disputer import dispute
@pytest.mark.asyncio
async def test_dispute():

    await dispute()