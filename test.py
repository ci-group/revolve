





async def evaluate_single_robot(self, individual, environment):
   """
   :param individual: individual
   :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
   """

   conf = copy.deepcopy(self.conf)
   conf.fitness_function = conf.fitness_function[environment]

   if self.analyzer_queue is not None:
      collisions, _bounding_box = await self.analyzer_queue.test_robot(individual,
                                                                       conf)
      if collisions > 0:
         logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
         return None, None

   return await self.simulator_queue[environment].test_robot(individual, conf)