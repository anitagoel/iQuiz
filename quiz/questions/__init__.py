from .question import *
from .mcq import MCQ
from .tfq import TFQ
from .saq import SAQ
from .vmcq import VMCQ

QUESTION_TYPE = {           # defines the name and class of the available type of questions.
    'MCQ': MCQ,
    'TFQ': TFQ,
    'SAQ': SAQ,
    'VMCQ': VMCQ,
}