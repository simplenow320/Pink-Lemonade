"""
Demonstrate the 3 levels of Smart Tools output quality
Users can choose based on their needs: speed, balance, or premium
"""

print("=" * 90)
print("QUALITY LEVELS COMPARISON - You Choose Based on Your Needs")
print("=" * 90)

print("\n\n📝 THANK YOU LETTER - Same donor, 3 different approaches:\n")

# LEVEL 1: Template Only (Fastest, Cheapest)
print("─" * 90)
print("LEVEL 1: TEMPLATE-ONLY (Instant, $0.0001)")
print("Best for: High-volume acknowledgments, recurring donors")
print("─" * 90)
template_only = """Dear Sarah Johnson,

Thank you for your generous contribution of $2,500 to Urban Youth Empowerment Center.

Your support transforms lives in our community. Because of supporters like you, we can expand our STEM Mentorship program and serve more Detroit youth.

This year alone, we served 350 young people with a 92% program completion rate - and that's just the beginning of what your generosity makes possible.

Together, we're building a stronger community.

Gratefully,
Marcus Williams
Executive Director
Urban Youth Empowerment Center"""

print(template_only)

# LEVEL 2: Hybrid (Balanced)
print("\n\n─" * 90)
print("LEVEL 2: HYBRID - TEMPLATE + MINIMAL AI (2 sec, $0.002)")
print("Best for: Most use cases - professional and personalized")
print("─" * 90)
hybrid = """Dear Sarah Johnson,

Thank you! Your generous contribution of $2,500 to Urban Youth Empowerment Center means more than words can express.

Your support transforms lives in our community. Because of supporters like you, we can expand our STEM Mentorship program.

Your belief in our mission to empower underserved youth inspires us to reach even higher. Thanks to supporters like you, we've seen our students achieve a 92% completion rate, and just last month, 15 of our graduates secured their first tech internships. Your investment is changing futures.

This year we served 350 young people - and that's just the beginning of what your generosity makes possible.

Together, we're building a stronger community.

Gratefully,
Marcus Williams
Executive Director
Urban Youth Empowerment Center"""

print(hybrid)

# LEVEL 3: Full AI (Premium)
print("\n\n─" * 90)
print("LEVEL 3: FULL AI (15 sec, $0.15)")
print("Best for: Major donors, special campaigns, VIP recognition")
print("─" * 90)
full_ai = """Dear Sarah,

Your extraordinary gift of $2,500 has arrived at exactly the right moment, and I wanted to personally reach out to express our profound gratitude.

When you chose to invest in Urban Youth Empowerment Center's STEM Mentorship program, you didn't just make a donation - you became a catalyst for transformation in Detroit. Your support represents more than dollars; it represents belief, hope, and a commitment to the next generation.

I wish you could have been in our classroom last Tuesday when Jasmine, a shy 17-year-old who joined us with no tech background, presented her first coding project to a panel of industry professionals. The confidence in her voice, the pride in her work - that's what your $2,500 creates. Jasmine is now heading to college with a full scholarship, planning to study computer science. She's one of 85 students we graduated this year with a remarkable 92% completion rate and 78% job placement success.

Your timing couldn't be better. With gifts like yours, we're expanding into two new Detroit neighborhoods this fall, which means 150 more young people will get the same chance Jasmine had. That's 150 more futures transformed, 150 more families lifted, 150 more reasons to believe in the power of education and mentorship.

Sarah, you're not just a donor to us - you're a partner in this movement. Every line of code our students write, every internship they secure, every barrier they break - you're part of that story.

Thank you for seeing the potential in our youth and investing in their dreams. Together, we're not just building skills; we're building a stronger, more equitable Detroit.

With deep appreciation and excitement for what's ahead,

Marcus Williams
Executive Director
Urban Youth Empowerment Center

P.S. I'd love to invite you to our Winter Showcase in December where you can meet students like Jasmine and see firsthand the impact of your investment. I'll send details soon!"""

print(full_ai)

print("\n\n" + "=" * 90)
print("COMPARISON SUMMARY:")
print("=" * 90)

comparison = """
┌─────────────────┬──────────────┬───────────────┬─────────────────┬────────────────────┐
│ Level           │ Generation   │ Cost          │ Personalization │ Best Use Case      │
│                 │ Time         │               │ Level           │                    │
├─────────────────┼──────────────┼───────────────┼─────────────────┼────────────────────┤
│ 1. Template     │ Instant      │ $0.0001      │ ⭐⭐            │ High volume,       │
│    Only         │ (<0.5 sec)   │              │                 │ recurring donors   │
├─────────────────┼──────────────┼───────────────┼─────────────────┼────────────────────┤
│ 2. Hybrid       │ Fast         │ $0.002       │ ⭐⭐⭐⭐        │ 90% of use cases   │
│    (RECOMMENDED)│ (2 sec)      │              │                 │ Perfect balance!   │
├─────────────────┼──────────────┼───────────────┼─────────────────┼────────────────────┤
│ 3. Full AI      │ Slow         │ $0.15        │ ⭐⭐⭐⭐⭐      │ Major donors,      │
│                 │ (15 sec)     │              │                 │ VIP recognition    │
└─────────────────┴──────────────┴───────────────┴─────────────────┴────────────────────┘

KEY INSIGHT: Level 2 (Hybrid) delivers 4-star personalization at 1% of the cost!

SMART USAGE STRATEGY:
• Use Level 1 (Template) for: Monthly donor acknowledgments, event thank yous
• Use Level 2 (Hybrid) for: Most individual donors, foundation grants, general use  ← DEFAULT
• Use Level 3 (Full AI) for: $10K+ gifts, board members, strategic partnerships
"""

print(comparison)

print("\n\n🎯 CUSTOMIZATION OPTIONS:")
print("─" * 90)
customization = """
You can also customize the hybrid level:

1. TONE VARIATION:
   • Formal - For foundations and corporate donors
   • Warm - For individual supporters (shown above)
   • Enthusiastic - For young professionals and millennial donors

2. LENGTH VARIATION:
   • Concise - 3 paragraphs (email-friendly)
   • Standard - 4-5 paragraphs (shown above)
   • Detailed - 6+ paragraphs (printed letters)

3. CONTENT EMPHASIS:
   • Impact-focused - Highlight outcomes and metrics
   • Story-driven - Feature beneficiary narratives
   • Future-oriented - Emphasize upcoming plans

4. SMART TRIGGERS (Auto-upgrade to Full AI when):
   • Donation amount > $5,000
   • First-time major donor
   • Lapsed donor returning
   • Special campaign milestone
   • Board member or VIP

Example: "Generate warm, concise, impact-focused thank you" → Perfect hybrid output in 2 seconds!
"""
print(customization)

print("\n" + "=" * 90)
print("YOUR POWER: Choose the right level for each situation!")
print("Save money on routine communications, invest in VIP relationships")
print("=" * 90)
