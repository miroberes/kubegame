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
            {"run": "openk8s", "expect": ["Correct magic key phrase! The gate opens and you see the village awaiting you to -enter-."]},
            {"run": "enter village", "expect": ["You entered the village, look around..."]},
            {"run": "describe village", "expect": ["small village"]},
            {
                "run": "lookaround",
                "expect": ["chimneysweep", "telephone-booth", "wizardshouse"],
                "absent": ["booth-telephone-pod", "telephone-operator"],
            },
            {"run": "call chimneysweep", "expect": ["Call wizard on his phone"]},
            {"run": "hey chimneysweep", "expect": ["Nice day, eh? Looking for the wizard?"]},
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
            {"run": "inspect telephone-book", "expect": ["Wizard: dial 8081"]},
            {"run": "describe booth-telephone", "expect": ["A telephone hangs on the wall of the booth"]},
            {"run": "inspect booth-telephone", "expect": ["A telephone hangs on the wall of the booth"]},
            {"run": "dial chimneysweep", "expect": ["There is nothing called chimneysweep here."]},
        ],
    },
    {
        "name": "The wizard's phone",
        "steps": [
            {"run": "dial 8081", "expect": ["dial 8081 Name"]},
            {"run": "dial 8081 Alice", "expect": ["Thank you, Alice. I will remember your name."]},
            {"run": "dial 8080", "expect": ["If you wait long enough"]},
        ],
    },
    {
        "name": "The wizard's house",
        "steps": [
            {"run": "enter wizardshouse Bob", "expect": ["The wizard has not let you in yet."]},
            {"run": "enter wizardshouse Alice", "expect": ["You entered the wizardshouse"]},
            {"run": "dial 8081", "expect": ["dial 8081 Name"]},
            {"run": "dial 8080", "expect": ["If you wait long enough"]},
            {"run": "inspect bookshelf-pod", "expect": ["The Pipeline Grimoire"]},
            {"run": "inspect postit-pod", "expect": ["Great power lives in its pages.", "kubectl apply -f ~/...yaml", "then:", "kubectl delete pod player-pod"]},
            {"run": "describe bookshelf-pod", "expect": ["The Pipeline Grimoire"]},
            {"run": "describe wizardshouse", "expect": ["A chimneysweep is on the roof, sweeping the chimney."]},
        ],
    },
    {
        "name": "Back to the village",
        "steps": [
            {"run": "enter village", "expect": ["You entered the village, look around..."]},
            {"run": "call chimneysweep", "expect": ["Call wizard on his phone"]},
        ],
    },
    {
        "name": "The book of spells",
        "steps": [
            {"run": "enter wizardshouse Alice", "expect": ["You entered the wizardshouse"]},
            {"run": "kubectl apply -f ~/k8s-spellkeeper.yaml", "expect": ["pod/k8s-spellkeeper-pod created", "configmap/book created"]},
            {"run": "sleep 6"},
            {"run": "enter village", "expect": ["You entered the village, look around..."]},
            {"run": "kubectl get pod k8s-spellkeeper-pod -n village -o name", "expect": ["pod/k8s-spellkeeper-pod"]},
            {"run": "call chimneysweep", "expect": ["Call wizard on his phone"]},
        ],
    },
]
