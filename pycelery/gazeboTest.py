import os
import sys
import asyncio
from pyrevolve.SDF.math import Vector3
from pyrevolve import revolve_bot, parser
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution import fitness

from pycelery.tasks import stupid, Gazebo_only

async def run():
    # wait a second to get celery started
    await asyncio.sleep(3)

    """Test 1: Asyncio -- Status: WORKS"""
    # result = await stupid.delay()
    # done = await result.get()
    #
    # print(done)

    """Test 2: Gazebo -- Status: working on"""
    gazebo = await Gazebo_only.delay()
    done = await gazebo.get()
