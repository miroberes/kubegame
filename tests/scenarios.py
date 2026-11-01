"""Game scenarios for the end-to-end layer.

Each scenario is a list of steps played in order in one game session, so later
scenarios build on the cluster state left by earlier ones.

A step types `run` into the game shell. `expect` lists text that must appear in
the output, and `absent` lists text that must not.
"""

SCENARIOS = [
    {
        "name": "Act 2 begins in the village",
        "steps": [
            {"run": "openk8s"},
            {"run": "enter village", "expect": ["You entered the village, look around..."]},
            {"run": "describe village", "expect": ["small village"]},
            {
                "run": "lookaround",
                "expect": ["chimneysweep", "poster-on-the-chimney", "telephone-booth", "wizardshouse"],
                "absent": ["booth-telephone-pod", "telephone-operator"],
            },
            {"run": "call chimneysweep", "expect": ["Call wizard on his phone"]},
        ],
    },
    {
        "name": "The telephone booth",
        "steps": [
            {"run": "enter telephone-booth", "expect": ["You entered the telephone-booth"]},
            {"run": "describe telephone-booth", "expect": ["recent calls: 8082, 8081, 7777"]},
            {
                "run": "lookaround",
                "expect": ["booth-telephone", "telephone-book"],
                "absent": ["booth-telephone-pod", "telephone-operator"],
            },
            {"run": "inspect telephone-book", "expect": ["Wizard: 8081"]},
            {"run": "describe booth-telephone", "expect": ["A telephone hangs on the wall of the booth"]},
            {"run": "dial chimneysweep", "expect": ["There is nothing called chimneysweep here."]},
        ],
    },
    {
        "name": "The wizard's phone",
        "steps": [
            {"run": "dial 8081", "expect": ["dial 8081 Name"]},
            {"run": "dial 8081 Alice", "expect": ["Thank you, Alice. I will remember your name."]},
        ],
    },
    {
        "name": "The wizard's house",
        "steps": [
            {"run": "enter wizardshouse", "expect": ["The wizard has not let you in yet."]},
            {"run": "describe wizardshouse", "expect": ["A house with a chimney stands in the village"]},
        ],
    },
]
