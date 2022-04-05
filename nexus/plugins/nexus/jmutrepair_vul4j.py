from nexus.plugins.nexus.jgenprog_vul4j import JGenProgVul4JRepairTask


class JMutRepairVul4JRepairTask(JGenProgVul4JRepairTask):
    class Meta:
        label = 'jmutrepair_vul4j'

    def __init__(self, **kw):
        super().__init__(tool='jmutrepair', benchmark='vul4j', **kw)


def load(app):
    app.handler.register(JMutRepairVul4JRepairTask)
