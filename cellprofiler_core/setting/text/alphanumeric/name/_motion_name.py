from ._name import Name


class MotionName(Name):
    def __init__(self, text, value="Motion", *args, **kwargs):
        super(MotionName, self).__init__(text, "motiongroup", value, *args, **kwargs)
