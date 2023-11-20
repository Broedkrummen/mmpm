#!/usr/bin/env python3
""" Command line options for 'mm-ctl' subcommand """
from mmpm.env import MMPMEnv
from mmpm.logger import MMPMLogger
from mmpm.magicmirror.controller import MagicMirrorController
from mmpm.subcommands.sub_cmd import SubCmd

logger = MMPMLogger.get_logger(__name__)


class MmCtl(SubCmd):
    def __init__(self, app_name):
        self.app_name = app_name
        self.name = "mm-ctl"
        self.help = f"Commands to interact with/control MagicMirror"
        self.usage = f"{self.app_name} {self.name} [--status] [--hide] [--show] [--start] [--stop] [--restart]"
        self.controller = MagicMirrorController()
        self.env = MMPMEnv()

    def register(self, subparser):
        self.parser = subparser.add_parser(self.name, usage=self.usage, help=self.help)

        self.parser.add_argument(
            "--status",
            action="store_true",
            help="show the hidden/visible status and key(s) of module(s) on your MagicMirror",
            dest="status",
        )

        self.parser.add_argument(
            "--hide",
            nargs="+",
            help="hide module(s) on your MagicMirror via provided key(s)",
            dest="hide",
        )

        self.parser.add_argument(
            "--show",
            nargs="+",
            help="show module(s) on your MagicMirror via provided key(s)",
            dest="show",
        )

        self.parser.add_argument(
            "--start",
            action="store_true",
            help="start MagicMirror; works with pm2 and docker-compose",
            dest="start",
        )

        self.parser.add_argument(
            "--stop",
            action="store_true",
            help="stop MagicMirror; works with pm2 and docker-compose",
            dest="stop",
        )

        self.parser.add_argument(
            "--restart",
            action="store_true",
            help="restart MagicMirror; works with pm2 and docker-compose",
            dest="restart",
        )

    def exec(self, args, extra):
        if extra:
            logger.msg.extra_args(args.subcmd)
        elif args.status:
            self.controller.status()
        elif args.hide:
            self.controller.hide_modules(args.hide)
        elif args.show:
            self.controller.show_modules(args.show)
        elif args.start:
            if self.env.mmpm_is_docker_image.get():
                logger.fatal("Cannot execute this command within a docker image")
            else:
                self.controller.start()
        elif args.stop:
            if self.env.mmpm_is_docker_image.get():
                logger.fatal("Cannot execute this command within a docker image")
            else:
                self.controller.stop()
        elif args.restart:
            if self.env.mmpm_is_docker_image.get():
                logger.fatal("Cannot execute this command within a docker image")
            else:
                self.controller.restart()
        else:
            logger.msg.no_args(args.subcmd)
