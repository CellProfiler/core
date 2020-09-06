from ._subscriber import Subscriber


class MotionSubscriber(Subscriber):
    def __init__(
        self,
        text,
        value="Do not use",
        can_be_blank=False,
        blank_text="Leave blank",
        *args,
        **kwargs,
    ):
        super(MotionSubscriber, self).__init__(
            text, "motiongroup", value, can_be_blank, blank_text, *args, **kwargs
        )
