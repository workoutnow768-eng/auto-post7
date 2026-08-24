"""
Content bank for the workout/fitness channel -- mirrors recipe_ideas.py's
shape exactly so it plugs straight into make_slides.py (copied into this
project as workout-page/scripts/make_slides.py, with one small addition:
customizable badge wording, since "STEP 2" doesn't fit a myth-busting post
the way it fits an exercise routine).

Each entry has:
  - "type": "routine" | "tip" -- not read by the renderer, just for us to
    track the mix so the feed doesn't become 100% straight workouts.
  - "title", "duration", "level": headline info for slide 1.
  - "slides": list of dicts (heading/sub/detail), same shape as recipes.
    Standing convention as of 2026-08-22 (per user request): aim for 4-5
    slides per post (intro + 3-4 steps), and give every step slide a
    substantial "detail" line, not just a short "sub" -- a real amount of
    coaching info per move/point, not a one-liner.
  - "caption", "hashtags": for the Buffer post text.
  - "badge_step" / "badge_intro": optional overrides so a routine says
    "MOVE 1" / "3 QUICK MOVES" while a tip post says "FACT 1" / "3 KEY FACTS".
    Falls back to "STEP" / "EASY STEPS" if omitted (same as recipes).

WHY THE MIX: pure exercise-routine content runs out fast -- there are only
so many distinct 3-move circuits before it feels repetitive. Interleaving
"tip" posts (form fixes, myth-busting, common mistakes, quick fitness
facts) keeps the same visual carousel format and posting cadence, but
draws on a much bigger well of content than "here's another workout" can
sustain alone. Suggested rotation: roughly 2 routines for every 1 tip post.
"""

WORKOUTS = [
    {
        "type": "routine",
        "title": "5-Minute Ab Burnout (No Equipment)",
        "duration": "5 min", "level": "All Levels",
        "badge_step": "MOVE", "badge_intro": "QUICK MOVES",
        "slides": [
            {"heading": "5-Min Ab Burnout", "sub": "Duration: 5 min  |  All Levels"},
            {"heading": "1. Plank Hold", "sub": "Hold a forearm plank, 40 sec", "detail": "Keep hips level with shoulders and squeeze your glutes -- a sagging or piked hip means the core stops doing the work."},
            {"heading": "2. Bicycle Crunch", "sub": "Alternating elbow to knee, 40 sec", "detail": "Slow the tempo down and fully rotate your ribcage toward the opposite knee -- speed without rotation just wastes the rep."},
            {"heading": "3. Leg Raises", "sub": "Flat back, lower slow, 40 sec", "detail": "Press your lower back into the floor throughout -- if it arches off the ground, shorten the range until it doesn't."},
            {"heading": "4. Russian Twists", "sub": "Feet lifted, rotate side to side, 40 sec", "detail": "Move slowly enough to feel your obliques doing the work, not your arms swinging a weight -- lean back just enough to keep tension on your core the whole time."},
        ],
        "caption": "5 minutes, zero equipment, real burn — no excuses today 🔥💪",
        "hashtags": "#absworkout #noequipment #homeworkout #corestrength #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "Beginner Leg Day (Bodyweight)",
        "duration": "15 min", "level": "Beginner",
        "badge_step": "MOVE", "badge_intro": "STARTER MOVES",
        "slides": [
            {"heading": "Beginner Leg Day", "sub": "Duration: 15 min  |  Beginner"},
            {"heading": "1. Bodyweight Squats", "sub": "3 sets of 12, controlled tempo", "detail": "Sit back like you're reaching for a chair and keep your weight in your heels -- knees caving inward is the most common beginner mistake here."},
            {"heading": "2. Reverse Lunges", "sub": "3 sets of 10 per leg", "detail": "Step back rather than forward to protect your knees while you're still building balance, and keep your torso upright through the whole movement."},
            {"heading": "3. Glute Bridges", "sub": "3 sets of 15, squeeze at the top", "detail": "Drive through your heels and pause for a full second at the top, squeezing your glutes hard before lowering back down."},
        ],
        "caption": "No gym, no gear — just a real beginner leg day that actually works 🦵",
        "hashtags": "#legday #beginnerworkout #bodyweight #homeworkout #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "3 Dumbbell Moves for Bigger Arms",
        "duration": "20 min", "level": "Intermediate",
        "badge_step": "MOVE", "badge_intro": "ARM BUILDERS",
        "slides": [
            {"heading": "Dumbbell Arm Builder", "sub": "Duration: 20 min  |  Intermediate"},
            {"heading": "1. Bicep Curls", "sub": "4 sets of 10, slow negatives", "detail": "Take 3 full seconds to lower the weight -- the slow negative is where most of the muscle-building tension actually happens."},
            {"heading": "2. Overhead Tricep Extension", "sub": "4 sets of 12", "detail": "Keep your elbows pointed forward and close to your head throughout -- letting them flare out shifts the work off the triceps."},
            {"heading": "3. Hammer Curls", "sub": "3 sets of 12 per arm", "detail": "Keep your palms facing each other the entire rep -- this grip hits the forearm and outer bicep differently than a standard curl."},
        ],
        "caption": "3 moves, one set of dumbbells, real arm growth 💪🏋️",
        "hashtags": "#armday #dumbbellworkout #bicepsandtriceps #gymtiktok #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "10-Minute Morning Mobility Routine",
        "duration": "10 min", "level": "All Levels",
        "badge_step": "MOVE", "badge_intro": "WAKE-UP MOVES",
        "slides": [
            {"heading": "Morning Mobility", "sub": "Duration: 10 min  |  All Levels"},
            {"heading": "1. Cat-Cow Stretch", "sub": "10 slow reps", "detail": "Move with your breath -- arch and drop your belly on the inhale, round your spine toward the ceiling on the exhale."},
            {"heading": "2. World's Greatest Stretch", "sub": "5 reps per side", "detail": "Sink deep into the lunge, plant your back hand down, and rotate your other arm toward the ceiling to open the whole side of your body."},
            {"heading": "3. Standing Forward Fold", "sub": "Hold 30 sec, knees soft", "detail": "Let your head and arms hang heavy and keep a slight bend in your knees -- this is about releasing tension, not forcing a stretch."},
        ],
        "caption": "10 minutes before coffee changes how your whole day feels 🌅🧘",
        "hashtags": "#morningroutine #mobility #stretching #wellness #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "Full Body Home Workout (No Equipment)",
        "duration": "20 min", "level": "Intermediate",
        "badge_step": "MOVE", "badge_intro": "FULL-BODY MOVES",
        "slides": [
            {"heading": "Full Body, No Gym", "sub": "Duration: 20 min  |  Intermediate"},
            {"heading": "1. Push-Ups", "sub": "4 sets of 12, chest to floor", "detail": "Keep your body in one straight line from head to heels the whole way down -- sagging hips turn this into a lower-back exercise instead."},
            {"heading": "2. Jump Squats", "sub": "4 sets of 15, land soft", "detail": "Land with bent knees and roll through the foot to absorb the impact -- landing stiff-legged is what actually causes knee soreness the next day."},
            {"heading": "3. Mountain Climbers", "sub": "4 sets of 30 sec", "detail": "Keep your hips low and stable, like you're holding a plank the whole time -- if your hips bounce up and down, slow the pace."},
        ],
        "caption": "Zero equipment, full body, done in 20 minutes flat 🏠💥",
        "hashtags": "#fullbodyworkout #noequipment #homeworkout #hiit #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "Resistance Band Booty Burner",
        "duration": "15 min", "level": "All Levels",
        "badge_step": "MOVE", "badge_intro": "BURNER MOVES",
        "slides": [
            {"heading": "Band Booty Burner", "sub": "Duration: 15 min  |  All Levels"},
            {"heading": "1. Banded Squats", "sub": "3 sets of 15, band above knees", "detail": "Actively push your knees out against the band on every rep -- the tension is the point, don't let the band go slack at the top."},
            {"heading": "2. Lateral Band Walks", "sub": "3 sets of 12 steps per side", "detail": "Stay low in a mini-squat the entire time and keep your toes pointed forward -- standing up between steps lets the band do nothing."},
            {"heading": "3. Banded Glute Bridges", "sub": "3 sets of 15, pause at top", "detail": "Press your knees outward against the band as you lift your hips, and hold a 2-second squeeze at the very top of each rep."},
        ],
        "caption": "One resistance band, 15 minutes, real glute burn 🍑🔥",
        "hashtags": "#glutesworkout #resistanceband #bootyworkout #homeworkout #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "Upper Body Push Day (Dumbbells)",
        "duration": "25 min", "level": "Intermediate",
        "badge_step": "MOVE", "badge_intro": "PUSH MOVES",
        "slides": [
            {"heading": "Dumbbell Push Day", "sub": "Duration: 25 min  |  Intermediate"},
            {"heading": "1. Dumbbell Bench Press", "sub": "4 sets of 10", "detail": "Lower the weights until your upper arms are roughly parallel to the floor, then press back up in a slight arc rather than straight up."},
            {"heading": "2. Shoulder Press", "sub": "4 sets of 10", "detail": "Press the dumbbells up and slightly inward so they nearly touch at the top -- pressing straight up without that angle overworks the front delts."},
            {"heading": "3. Push-Up Finisher", "sub": "3 sets to near failure", "detail": "Go until your form starts to break down, not until you physically collapse -- a few clean reps beat a lot of sloppy ones."},
        ],
        "caption": "Chest, shoulders, triceps — one push day, done right 💪🏋️",
        "hashtags": "#pushday #dumbbellworkout #chestworkout #gymtiktok #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "Core Stability Routine",
        "duration": "10 min", "level": "All Levels",
        "badge_step": "MOVE", "badge_intro": "STABILITY MOVES",
        "slides": [
            {"heading": "Core Stability", "sub": "Duration: 10 min  |  All Levels"},
            {"heading": "1. Dead Bug", "sub": "3 sets of 10 per side", "detail": "Press your lower back flat into the floor and move the opposite arm and leg together, slowly -- speed here just means you're cheating the core out of work."},
            {"heading": "2. Side Plank", "sub": "3 sets, 30 sec per side", "detail": "Stack your hips and shoulders in one straight line and lift your top hip slightly toward the ceiling -- a sagging hip is the giveaway your core has checked out."},
            {"heading": "3. Bird Dog", "sub": "3 sets of 10 per side", "detail": "Extend opposite arm and leg without letting your hips rotate open -- imagine balancing a cup of water on your lower back."},
        ],
        "caption": "Real core stability, not just another ab burnout 🧘‍♀️💪",
        "hashtags": "#corestability #coreworkout #homeworkout #fitnesstiktok #wellness",
    },
    {
        "type": "routine",
        "title": "HIIT Cardio Blast (No Equipment)",
        "duration": "15 min", "level": "Intermediate",
        "badge_step": "ROUND", "badge_intro": "HIIT ROUNDS",
        "slides": [
            {"heading": "HIIT Cardio Blast", "sub": "Duration: 15 min  |  Intermediate"},
            {"heading": "1. Burpees", "sub": "40 sec on, 20 sec rest, x3", "detail": "Scale the jump at the top to a reach or step-up if needed -- the goal is keeping intensity high for the full 40 seconds, not perfect form on a move you're rushing."},
            {"heading": "2. High Knees", "sub": "40 sec on, 20 sec rest, x3", "detail": "Drive your knees up toward hip height and pump your arms hard -- this is meant to spike your heart rate, so treat it like a sprint, not a jog in place."},
            {"heading": "3. Squat Jumps", "sub": "40 sec on, 20 sec rest, x3", "detail": "Land soft with bent knees every single rep -- fatigue is when landing form breaks down, so slow down before your knees pay for it."},
        ],
        "caption": "15 minutes of real HIIT — no equipment, no excuses 🔥⏱️",
        "hashtags": "#hiitworkout #cardioblast #noequipment #fatburn #fitnesstiktok",
    },
    {
        "type": "routine",
        "title": "Back & Biceps Pull Day",
        "duration": "25 min", "level": "Intermediate",
        "badge_step": "MOVE", "badge_intro": "PULL MOVES",
        "slides": [
            {"heading": "Pull Day: Back & Biceps", "sub": "Duration: 25 min  |  Intermediate"},
            {"heading": "1. Bent-Over Rows", "sub": "4 sets of 10", "detail": "Hinge from your hips with a flat back and pull the weight toward your lower ribs -- pulling toward your chest instead shifts the work onto your shoulders."},
            {"heading": "2. Lat Pulldowns", "sub": "4 sets of 12", "detail": "Pull the bar to your upper chest while leaning back only slightly -- using momentum to yank the bar down skips the muscle you're trying to train."},
            {"heading": "3. Dumbbell Curls", "sub": "3 sets of 12", "detail": "Keep your elbows pinned to your sides through the whole rep -- letting them swing forward turns a bicep curl into a shoulder exercise."},
        ],
        "caption": "Back and biceps, one clean pull day 💪🔙",
        "hashtags": "#pullday #backworkout #bicepsworkout #gymtiktok #fitnesstiktok",
    },
    {
        "type": "tip",
        "title": "Form Fix: The Squat",
        "duration": "Quick Read", "level": "All Levels",
        "badge_step": "FIX", "badge_intro": "COMMON MISTAKES",
        "slides": [
            {"heading": "Form Fix: The Squat", "sub": "The #1 mistake — and how to fix it"},
            {"heading": "1. The Mistake", "sub": "Knees caving inward on the way up", "detail": "This usually happens when the weight is too heavy or the glutes aren't firing hard enough to keep the knees tracking in line with the toes."},
            {"heading": "2. The Fix", "sub": "Actively push your knees outward", "detail": "Imagine spreading the floor apart with your feet on every rep -- this single cue engages the glutes and stops the inward knee collapse almost instantly."},
            {"heading": "3. Try This", "sub": "Loop a band above your knees to drill it", "detail": "The light resistance gives you instant feedback the moment your knees start to cave, which makes the correct pattern much faster to learn."},
            {"heading": "4. Double-Check", "sub": "Film yourself from the front on your next set", "detail": "Knee cave is often invisible from your own point of view mid-lift -- a 10-second phone clip from straight ahead will show you the truth instantly."},
        ],
        "caption": "Your squats might be quietly wrecking your knees — here's the fix 🦵🔧",
        "hashtags": "#squatform #formcheck #fitnesstips #gymtiktok #fitnesstiktok",
    },
    {
        "type": "tip",
        "title": "Myth vs Fact: Does Cardio Kill Gains?",
        "duration": "Quick Read", "level": "All Levels",
        "badge_step": "FACT", "badge_intro": "KEY FACTS",
        "slides": [
            {"heading": "Myth vs Fact", "sub": "Does cardio really kill your gains?"},
            {"heading": "1. The Myth", "sub": "\"Any cardio will eat your muscle\"", "detail": "This idea comes from extreme endurance training, not from a couple of moderate cardio sessions layered onto a normal lifting week."},
            {"heading": "2. The Fact", "sub": "Moderate cardio barely affects muscle growth", "detail": "Research on concurrent training shows 2-3 sessions of moderate cardio a week has little to no negative effect on strength or size gains for most lifters."},
            {"heading": "3. The Takeaway", "sub": "Keep cardio and lifting on separate days if possible", "detail": "Spacing them out reduces leftover fatigue so your lifting sessions stay strong, but doing both isn't the muscle-loss disaster it's made out to be."},
        ],
        "caption": "The \"cardio kills gains\" myth needs to die — here's the actual research 🏃‍♂️💪",
        "hashtags": "#cardiomyth #fitnessfacts #gymtok #fitnesstips #fitnesstiktok",
    },
    {
        "type": "tip",
        "title": "3 Signs You're Overtraining",
        "duration": "Quick Read", "level": "All Levels",
        "badge_step": "SIGN", "badge_intro": "WARNING SIGNS",
        "slides": [
            {"heading": "3 Signs of Overtraining", "sub": "Your body is telling you something"},
            {"heading": "1. Sleep Gets Worse", "sub": "Trouble falling or staying asleep", "detail": "Chronically elevated cortisol from too much training without recovery can paradoxically make it harder to fall and stay asleep, not easier."},
            {"heading": "2. Performance Stalls or Drops", "sub": "Lifts feel heavier than usual", "detail": "If weights that used to feel manageable suddenly feel much harder for no clear reason, that's often accumulated fatigue talking, not a bad day."},
            {"heading": "3. You're Getting Sick More Often", "sub": "Frequent colds or low energy", "detail": "Training without adequate recovery suppresses immune function over time, which is why overtrained athletes tend to catch every cold going around."},
        ],
        "caption": "More isn't always better — here's when to actually take a rest day 😴🚩",
        "hashtags": "#overtraining #recovery #fitnesstips #restday #fitnesstiktok",
    },
    {
        "type": "tip",
        "title": "Do You Really Need Rest Days?",
        "duration": "Quick Read", "level": "All Levels",
        "badge_step": "FACT", "badge_intro": "KEY FACTS",
        "slides": [
            {"heading": "Do You Need Rest Days?", "sub": "Yes — here's what's actually happening"},
            {"heading": "1. Muscle Grows at Rest", "sub": "Not during the workout itself", "detail": "Training creates micro-tears in muscle fibers; the actual growth and repair happens in the 24-72 hours after, fueled by protein and sleep."},
            {"heading": "2. Skipping Rest Slows Progress", "sub": "Under-recovered muscles lift less", "detail": "Training the same muscle group again before it's recovered means you're working with less strength available, which quietly caps your results over time."},
            {"heading": "3. Active Recovery Still Counts", "sub": "Walking or light stretching is fine", "detail": "A true rest day doesn't have to mean total inactivity -- easy movement can actually speed up recovery by improving blood flow to sore muscles."},
        ],
        "caption": "Rest days aren't laziness — they're literally where the gains happen 😴💪",
        "hashtags": "#restday #recovery #fitnessfacts #gymtok #fitnesstiktok",
    },
]


def get_workout_for_day(day_index):
    return WORKOUTS[day_index % len(WORKOUTS)]
