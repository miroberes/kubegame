# Kubernetes Kingdom: Developer Brief

**Spoiler warning:** Everything below reveals solutions.

## Act I: The Gate (`default` namespace)

| Step | Player action | Solution | Result | Source | Status |
|---|---|---|---|---|---|
| 1. Start | Reads the welcome page | `curl startgame` | Shows plot and first quest | `default/instructionspod.yaml`, `startgamesvc.yaml` | Done |
| 2. Inspect gate | Reads gate logs | `kubectl logs gate -c cluelogger` | "Whisper the magic key phrase... under the doormat" | `default/gatepod.yaml` | Done. README's `inspect` alias uses `-c main-container`, which doesn't exist here |
| 3. Find phrase | Runs `clue` (or `kubectl exec gate -c cluelogger -- ls /doormat`), then reads `/doormat/magic-key-phrase` | "look under the doormat" from `clue`; phrase stored in the `doormat` ConfigMap | `image/manifests/06-doormat.yaml`, `07-clue.yaml` | Done |
| 4. Whisper | Speaks the phrase | `whisper openplease` (`kubectl exec gate -c cluelogger -- sh /scripts/check_phrase.sh openplease`) | "Correct... Use the command: open gate"; sets `gate` to `unlocked` | `gatepod.yaml` | Done |
| 5. Open gate | Runs the command | `open gate` | Creates the `act2-player` RoleBinding in `village` and sets `act` to 2 | `commands.d/act1.rc`, `gatepod.yaml` | Done |
## Act II: The Village (`village` namespace)

| Step | Player action | Solution | Result | Source | Status |
|---|---|---|---|---|---|
| 5. Enter village | Runs the command | `switch village` (`kubectl config set-context --current --namespace village`) | Unlocks village | None | Undefined. No `village` namespace manifest exists |
| 6. Read poster | Calls the chimney sweep | `kubectl exec player -it -- wget -O - chimneysweep` | "Call wizard on his phone..." | `chimneysweep.yaml`, `poster-on-the-chimney.yaml` | Done. Poster logs hint at the chimney |
| 7. Call wizard | Dials the wizard | `wget -O - telephone:8081` | "Use the command: enter wizardshouse" | `telephone-operatorpod.yaml`, `telephonesvc.yaml` | Partial. See conflicts below |
| 8. Enter wizard's house | Runs the command | `enter wizardshouse` | Door opens | None | Undefined. Entering the house is not designed yet; nothing follows this step |
| 9. Call Tooth Fairy | Dials port 8082 | `wget -O - telephone:8082` | Voicemail: teeth, gifts, "tooth's special story" | `toothfairymessagecm.yaml` | Partial. No reward mechanic |
| 10. Booth clue | Reads booth logs | `kubectl logs telephone-booth` | Recent calls: 8082, 8081, 7777 | `telephone-boothpod.yaml` | 7777 leads nowhere |

## Act III: Roles (not started)

- After unlocking a namespace, a command updates the player's role.
- Players switch context to another user to gain access.
- Players learn to create CSRs for users.

No manifests exist for this act.

## Open issues

1. **Port 8082 conflict:** `wizardsphone.yaml` says "Wrong number," while the operator pod serves the Tooth Fairy.
2. **Duplicate `telephone` Services:** `wizardsphone.yaml` and `telephonesvc.yaml` both define `telephone` in `village`.
3. **Player pod name:** `player.yaml` names it `playerpod`. The README uses `player`.
4. **Undefined commands:** `use` has no defined role. `sns` was renamed to `switch` (see `kubernetes-kingdom-design.md`, section 4). `call`, `whisper`, and `lookaround` aren't implemented as aliases yet.
5. **Spoiler leak:** The phrase is in plain text in `gatepod.yaml`.
6. **Undefined story:** The curse, the 7777 line, the wizard's house, and the Tooth Fairy's reward have no content.
