import asyncio

from pyrevolve import parser
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.tol.manage import World


async def run():

	settings = parser.parse_args()
	yaml_file = 'experiments/'+ settings +'/data_fullevolution/phenotypes/'+'phenotype_'+settings.test_robot+'.yaml'

	r = RevolveBot(_id=settings.test_robot)
	r.load_file(yaml_file, conf_type='yaml')
	#r.save_file('experiments/'+ settings +'/data_fullevolution/phenotype_35.sdf.xml', conf_type='sdf')
	#r.render_body('experiments/'+ settings +'/data_fullevolution/phenotypes/phenotype_35.body.png')

	connection = await World.create(settings, world_address=("127.0.0.1", settings.port_start))
	await connection.insert_robot(r)


def main():
	import traceback

	def handler(_loop, context):
		try:
			exc = context['exception']
		except KeyError:
			print(context['message'])
			return
		traceback.print_exc()
		raise exc

	try:
		loop = asyncio.get_event_loop()
		loop.set_exception_handler(handler)
		loop.run_until_complete(run())
	except KeyboardInterrupt:
		print("Got CtrlC, shutting down.")


if __name__ == '__main__':
	print("STARTING")
	main()
	print("FINISHED")
