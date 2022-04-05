from nexus.plugins.nexus.jgenprog_vul4j import JGenProgVul4JRepairTask


class JKaliVul4JRepairTask(JGenProgVul4JRepairTask):
    class Meta:
        label = 'jkali_vul4j'

    def __init__(self, **kw):
        super().__init__(tool='jkali', benchmark='vul4j', **kw)


def load(app):
    app.handler.register(JKaliVul4JRepairTask)
