---
updated: generated
generator: build/make_docs.py - do not edit
authority: current
invalidated-by: adding or changing a patch stage
---

# Patch chain

Generated. Discovered by following SHA-256 links from the pinned upstream
bundle, so this table also proves the chain is linear, complete, and ends
at what ships.

- pinned upstream bundle: `a561c9f0a86560313b7165758e131b3140807482ba140922035c810f0d7f5631`
- shipping bundle:        `d24fc503a1d812934b081709608d56d30bbbb5e89d9ddf017910afeed2857c43`
- patch scripts:           **26**
- numbered patches:        **31** - the first script applies the
  original six fixes in one stage, so script count and patch number differ by five

| # | script | artifact | effect |
|---|---|---|---|
| 1 | `glpal_patch.py` | `glpal-index-editable.js` | Deterministic patcher for the GLPal deployed application bundle analyzed on 2026-08-13 |
| 2 | `glpal_patch7_dates.py` | `glpal-index-dates.js` | fix the date off-by-one in DISPLAY code only |
| 3 | `glpal_patch8_brand.py` | `titrate-index.js` | rebrand to "Titrate" |
| 4 | `glpal_patch9_goalweight.py` | `titrate-index-goal.js` | fix the goal-weight picker flashing open and vanishing |
| 5 | `glpal_patch10_goalunit.py` | `titrate-index-unit.js` | goal weight displayed with the height converter |
| 6 | `glpal_patch11_charty.py` | `titrate-index-chart.js` | weight chart y-axis bounds |
| 7 | `glpal_patch12_chartperiod.py` | `titrate-index-period.js` | the Week/Month/90 Days/All Time selector does nothing on the weight chart |
| 8 | `glpal_patch13_currentlevel.py` | `titrate-index-level.js` | show the current medication level on the dose chart |
| 9 | `glpal_patch14_samplenow.py` | `titrate-index-now.js` | show today's partial absorption instead of zero |
| 10 | `glpal_patch15_trim.py` | `titrate-index-trim.js` | hide the Peptides and Calculator sections |
| 11 | `glpal_patch16_totaldoses.py` | `titrate-index-total.js` | the "Total Doses" card counts plan doses, not doses |
| 12 | `glpal_patch17_layout.py` | `titrate-index-layout.js` | dashboard layout and a Log tab rename |
| 13 | `glpal_patch18_cards.py` | `titrate-index-cards.js` | dashboard card set and order |
| 14 | `glpal_patch19_bestcards.py` | `titrate-index-best.js` | drop the Best Week and Best Month cards |
| 15 | `glpal_patch20_bateman.py` | `titrate-index-bateman.js` | Bateman-curve medication level model |
| 16 | `glpal_patch21_axisyear.py` | `titrate-index-axisyear.js` | year-qualified chart axis categories |
| 17 | `glpal_patch22_dosetime.py` | `titrate-index-dosetime.js` | place each dose at its recorded time, not local midnight |
| 18 | `glpal_patch23_wyelevel.py` | `titrate-index-wyelevel.js` | remove the unused medication-level calculation from the dosing-plan hook |
| 19 | `glpal_patch24_progressbar.py` | `titrate-index-progressbar.js` | stop the Doses screen crashing when a dosing plan is active |
| 20 | `glpal_patch25_nodemo.py` | `titrate-index-nodemo.js` | remove the "Load Sample Data (Demo)" button from Settings |
| 21 | `glpal_patch26_nostorage.py` | `titrate-index-nostorage.js` | hide medication storage |
| 22 | `glpal_patch27_noplans.py` | `titrate-index-noplans.js` | hide dosing plans |
| 23 | `glpal_patch28_buttonlabels.py` | `titrate-index-labels.js` | rename two buttons |
| 24 | `glpal_patch29_dosecalc.py` | `titrate-index-dosecalc.js` | dosage calculator under the Log Dose button on the Doses tab |
| 25 | `glpal_patch30_avgpeak.py` | `titrate-index-avgpeak.js` | "Avg Peak (14d)" card on the Doses tab |
| 26 | `glpal_patch31_calclayout.py` | `titrate-index-calclayout.js` | dosage calculator: results above the input, always shown |

## SHA-256 links

| stage | input | output |
|---|---|---|
| _upstream capture_ | — | `a561c9f0a86560313b7165758e131b3140807482ba140922035c810f0d7f5631` |
| `glpal_patch.py` | `a561c9f0a86560313b7165758e131b3140807482ba140922035c810f0d7f5631` | `dbea7baaff958b56a4567c1a984c9b7a46ef696b792412bd1279e7433f75236e` |
| `glpal_patch7_dates.py` | `dbea7baaff958b56a4567c1a984c9b7a46ef696b792412bd1279e7433f75236e` | `13971fbc564d4b3df7c6317ad65843b64d1b5c58ea9fc1fcc07b6efcfd68e67f` |
| `glpal_patch8_brand.py` | `13971fbc564d4b3df7c6317ad65843b64d1b5c58ea9fc1fcc07b6efcfd68e67f` | `4d5953e0277df472e98da30315afda51bee0bab43de9b2021844bf03a10e148a` |
| `glpal_patch9_goalweight.py` | `4d5953e0277df472e98da30315afda51bee0bab43de9b2021844bf03a10e148a` | `cd67d85fc07934caf3c2e23395fc713660ddda0fe611cea244470029a3761aff` |
| `glpal_patch10_goalunit.py` | `cd67d85fc07934caf3c2e23395fc713660ddda0fe611cea244470029a3761aff` | `e1330709887aeb115ac65dc0023e9372e8c7056b1161d77a51a703d1773a66ab` |
| `glpal_patch11_charty.py` | `e1330709887aeb115ac65dc0023e9372e8c7056b1161d77a51a703d1773a66ab` | `37638391810ef2babbee71c5482db5c6bc49fe8d3163b2a9a54d78326b4dfd69` |
| `glpal_patch12_chartperiod.py` | `37638391810ef2babbee71c5482db5c6bc49fe8d3163b2a9a54d78326b4dfd69` | `5797758f0e14262c54051165c93129eb91d9c5e2905716a0b07a08f95d1c9a76` |
| `glpal_patch13_currentlevel.py` | `5797758f0e14262c54051165c93129eb91d9c5e2905716a0b07a08f95d1c9a76` | `0290848e7b5db004b190a76a8af3dc74b3b17ec093fa5ad6e544d7cef59d99c5` |
| `glpal_patch14_samplenow.py` | `0290848e7b5db004b190a76a8af3dc74b3b17ec093fa5ad6e544d7cef59d99c5` | `1b5d6f0bb61a7f9308085186783727d71f9ce4ae441f1ecf0b728e24155b6a35` |
| `glpal_patch15_trim.py` | `1b5d6f0bb61a7f9308085186783727d71f9ce4ae441f1ecf0b728e24155b6a35` | `14e161b18f1950a00b03de32ef3427bc1352a0b18caefddef01952766d815e1a` |
| `glpal_patch16_totaldoses.py` | `14e161b18f1950a00b03de32ef3427bc1352a0b18caefddef01952766d815e1a` | `c12bae59191c5f5b86da0060a2719e890614b43bac5af918cdbcc4b7da5af780` |
| `glpal_patch17_layout.py` | `c12bae59191c5f5b86da0060a2719e890614b43bac5af918cdbcc4b7da5af780` | `c388a97543015b78bbb3de446fee4e40aea0ef7898332ed2a6f79826fcd37e5a` |
| `glpal_patch18_cards.py` | `c388a97543015b78bbb3de446fee4e40aea0ef7898332ed2a6f79826fcd37e5a` | `46b1164aab5818c1f3dd8f7f8ba4db398205a1123429188f2eeceff14c7242e2` |
| `glpal_patch19_bestcards.py` | `46b1164aab5818c1f3dd8f7f8ba4db398205a1123429188f2eeceff14c7242e2` | `ff23c8f4593df5cefd946aba41b7f013de7274d8e3aad40326c0f87befe1d786` |
| `glpal_patch20_bateman.py` | `ff23c8f4593df5cefd946aba41b7f013de7274d8e3aad40326c0f87befe1d786` | `78f6ca4ca7b000a6ebf44601a4d9caff1b4790852d38a1914fe58c7be043945d` |
| `glpal_patch21_axisyear.py` | `78f6ca4ca7b000a6ebf44601a4d9caff1b4790852d38a1914fe58c7be043945d` | `d02bc0329c5c0fd7d8629d26f3944bafdf349bbdf658013da4428dc4cdaf941a` |
| `glpal_patch22_dosetime.py` | `d02bc0329c5c0fd7d8629d26f3944bafdf349bbdf658013da4428dc4cdaf941a` | `25c35ae27dbaacf6ba5573278fe454ad1ffe8a6c9e3e75b0044ee69ab4cf76e3` |
| `glpal_patch23_wyelevel.py` | `25c35ae27dbaacf6ba5573278fe454ad1ffe8a6c9e3e75b0044ee69ab4cf76e3` | `9a2e5b39cb4d253cdea5b8c66a985adff38154adaf8426dd68e62741b0449019` |
| `glpal_patch24_progressbar.py` | `9a2e5b39cb4d253cdea5b8c66a985adff38154adaf8426dd68e62741b0449019` | `cb28ba6620061907c58b525223183d4918a615a471049856e72e2680da9db723` |
| `glpal_patch25_nodemo.py` | `cb28ba6620061907c58b525223183d4918a615a471049856e72e2680da9db723` | `8334d584743780575f8f1ec04809f170feb4699f27a3df604c24a886809d22a7` |
| `glpal_patch26_nostorage.py` | `8334d584743780575f8f1ec04809f170feb4699f27a3df604c24a886809d22a7` | `055531610e1c54a3488a0bfb9b1a181072fdc6972b78357b38449bd126ce5eda` |
| `glpal_patch27_noplans.py` | `055531610e1c54a3488a0bfb9b1a181072fdc6972b78357b38449bd126ce5eda` | `13295d53d2b17ac6a543df812bfc5a7ea6358603f46df32f36afca79ed042371` |
| `glpal_patch28_buttonlabels.py` | `13295d53d2b17ac6a543df812bfc5a7ea6358603f46df32f36afca79ed042371` | `535bdacccaed7c4d48b671990266bb6b7a5dd2667fd4f2bdd5068e9eb12f9352` |
| `glpal_patch29_dosecalc.py` | `535bdacccaed7c4d48b671990266bb6b7a5dd2667fd4f2bdd5068e9eb12f9352` | `a9ba5fcf6250d8fab2b230eadfd0c54aed4f5507dc955de7d0769f8494453a4e` |
| `glpal_patch30_avgpeak.py` | `a9ba5fcf6250d8fab2b230eadfd0c54aed4f5507dc955de7d0769f8494453a4e` | `49111672aaba7538524bff25b5fd9d243f2aa48f6895d2c94925c666228f69fd` |
| `glpal_patch31_calclayout.py` | `49111672aaba7538524bff25b5fd9d243f2aa48f6895d2c94925c666228f69fd` | `d24fc503a1d812934b081709608d56d30bbbb5e89d9ddf017910afeed2857c43` |

`SHIP_SHA` matches the end of the chain.

The recolour stage runs after the last patch and is not SHA-pinned; it is
verified instead by `recolour.py` failing if any mapped colour survives.
