# Phase 1: Ideation, Market Validation and Feasibility

**Team 13:** Donirvin Dickerson, Jesus Quiroz, Javier Jacobo, Joanna Lim

## Industry and Target User
Consumer fitness and wellness. Target users are adults who are new to a gym, or returning after a long break, and want to exercise but do not know where to start. The problem occurs before entering the gym and on the gym floor: users have a goal (e.g. lose weight, gain muscle) but lack knowledge of which exercises to do.

## Problem Definition
- Uncertainty about where to start, how much to do, and whether an exercise is appropriate.
- Beginners rely on assumptions or online research that may not suit them.
- Pain or joint discomfort adds uncertainty (change the exercise, stop, or seek professional advice?), which can lead users to postpone, abandon routines, or continue movements that cause discomfort.

Public guidance recommends beginning slowly and increasing activity over time. A plan fitted to the user could make first steps clearer and easier to repeat. That extended benefit is a project hypothesis, not a demonstrated outcome.

## Proposed Solution
A fitness app that turns a short onboarding conversation into a beginner workout plan.
- **Inputs:** goal, experience level, days/times available, accessible equipment, movement preferences or limitations.
- **Outputs:** weekly schedule with exercises, sets and reps, plain-language instructions, and recommended substitutions.
- Users can review the plan, replace exercises, and report whether a workout felt too easy or too difficult so later suggestions adjust.

**Secondary feature:** users describe discomfort and its location. For ordinary mild discomfort, the app suggests lower-impact substitutes or stretches from a reviewed exercise library and reminds the user to stop if symptoms worsen. The app does not diagnose pain or promise treatment. Severe or worsening pain, pain following an injury, or other concerning symptoms lead to advice to seek professional care instead of an exercise recommendation. Safety rules and exercise content will be validated before this feature goes beyond the initial prototype.

## AI Application
AI creates and adjusts beginner plans using goal, experience, schedule, equipment, and above all limitations. An LLM interprets natural-language responses and personalizes recommendations, while a reviewed exercise library keeps suggestions safe and consistent. It handles varied combinations of needs more flexibly than a rule-based system.

## Initial Scope
The prototype includes:
1. Short onboarding (goals, experience, schedule, equipment, limitations).
2. AI-generated beginner workout plan.
3. Simple feedback (too easy / too difficult) used to adjust the plan.

## Market and Existing Solutions
Marketed to all fitness levels, primarily beginners. Similar apps: SmartGym, LADDER, Fitbod. We differentiate by focusing on beginner barriers: choosing realistic routines and feasible exercises, using gym equipment, and targeting desired muscle groups properly.

## Business Feasibility
Basic plans free; more personalized features via paid subscription. Costs: AI model usage, development, database hosting, maintenance. Value: affordable personalized guidance without a personal trainer.

## Technical Approach
Hybrid of LLM, NLP, and recommendation:
- **NLP** identifies goals, preferences, and limitations from natural-language input.
- **Recommendation system** uses that to select a beginner-friendly plan and exercises.
- **LLM** presents the plan concisely, explaining why an exercise is recommended or excluded.

## Data Plan
A small library of exercise names, muscle groups, instructions, and difficulty level. If an external dataset is used, licenses will be verified thoroughly. No medical records or sensitive personal information are needed, except age and weight.

## Risks
- **Privacy:** fitness info collection, API data sharing, retention, security.
- **Bias:** recommendations may not suit differing experience levels, abilities, equipment access, or goals.
- **Safety:** unsuitable intensity, limitations, and exercise guidance.
- **Business:** existing alternatives (differentiation), pricing, customer demand.
- **Feasibility:** output reliability, integration effort, cost, response time, testing.

## Milestones
1. **Data preparation:** identify data source, determine licensing, build structured library, review descriptions.
2. **AI proof of concept:** define onboarding, connect LLM API, generate workouts.
3. **Testing and evaluation.**
