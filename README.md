--- provide initial scene, like in Goblins, setting the objective

--- provide inventory - text files named after tools needed
-- possibly create new tools on the fly as game progresses

--- use pods as tools, for example to decode messages use a decoder pod, which runs a script decoding a key
-- you need to provide the right ingredients for the pod to be able to decode the key, like mandragora root or other things, players need to find somewhere

--- first scene
an aliased kubectl command like 'startgame' calls an website server (nginx) whose response tells the player he should find the key 
#players can ask for clues, again served by a website servers, calling clue, which returns 'search under the doormat'

   Welcome to the Kubernetes Kingdom Adventure!
   
   Plot: A mysterious curse has befallen the kingdom. Only the brave who master Kubernetes commands can unlock its secrets and lift the curse.
   
   First Quest: Inspect the "gate" pod to discover how to open the gate and begin your journey.
   
   Good luck!
alias lookaround='k get po,svc'

alias inspect='k logs -c main-container ' 
use like
inspect gate

  - command:
    - /bin/sh
    - -c
    - echo 'To open you need to 'whisper' the magic key phrase...' > /dev/stderr;
      sleep infinity
    image: busybox



-- find out how to open the gate = whisper the magic-key-phrase hidden under doormat directory to the gate pod
alias whisper="kubectl exec -it gate -- sh /scripts/check_phrase.sh "
-- gate opens providing further info about where it leads

--- village namespace
there is a house with a chimney where there is a poster but too far to read.
inspect poster - logs from the poster give clues, to lookaround and find a way to get to the poster
player needs to 'call' chimneysweep

--- user can not view namespaces per role
-- after unlocking a namespace, the role should be updated by issuing a "spell".
- proposition
to get a new role, player switches to a new context in which he is another user with another role, allowing to see more
-- learn to create csr for users

--- play sound when an action is done - ask AI how to do it

players start in the default namespace.
a player is represented by the pod player
k run player --image busybox:musl --command -- sh -c "sleep infinity"

To "do things", player needs to issue kubectl commands and their aliases as spells, edit existing kubernetes objects.
for example - kubectl exec player -it -- ...

there is a player pod in each of the namespaces, having role and rolebinding for the current namespace ???

Now that the gate is open, let us design the first quest.
The next scene is the namespace named village.
The scene consists of a house with a chimney on which there is a poster hanging with some text.
the poster is represented by a pod hosting an nginx app, which has the text on its index.html file // TODO replace the nginx container with a lightway index.html serving app
exposed by a service called 'chimneysweep'
to read the poster player needs to call the 'chimneysweep' service

alias use='kubectl exec player -it -- wget -O - '
call chimneysweep

poster says, you need to call the house owner (wizard container) to come to let you in
create a 'telephone' - service with a pod to 'call' the wizard container
the telephone is a service with a pod, which calls another service provided as a parameter
- create a telephone book pod to lookup numbers
- create a port-interceptor (AI) which routes non existing ports to an nginx error outputing container 
