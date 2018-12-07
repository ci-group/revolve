from .joint import Joint, Limit
from ..util import number_format as nf

class FixedJoint(Joint):
    """
    Implements a shortcut fixed joint; SDF currently does not support
    such a joint, so this is really a revolute joint with fixed limits.
    """

    def __init__(self, parent, child, axis=None, name=None, cfm=1e-7, erp=0.1):
        """

        :param parent:
        :param child:
        :return:
        """
        super(FixedJoint, self).__init__("revolute", parent, child, axis=axis, name=name)
        self.axis.limit = Limit(lower=0, upper=0, effort=0, velocity=0)
        self.cfm = cfm
        self.erp = erp
    
    def render_elements(self):
        """
        Add error reduction / constraint force mixing parameters.
        :return:
        """
        els = super(FixedJoint, self).render_elements()
        physics = []
        if self.cfm is not None:
            physics.append("<cfm>%s</cfm>" % nf(self.cfm))

        if self.erp is not None:
            physics.append("<erp>%s</erp>" % nf(self.erp))

        if physics:
            els += ["<physics><ode>" + "".join(physics) + "</ode></physics>"]

        return els
