"""
Content Library for Smart Tools
Pre-written, proven content blocks that can be assembled without AI
"""

from typing import Dict, List, Any

class ContentLibrary:
    """Repository of proven content templates and components"""
    
    @staticmethod
    def get_thank_you_templates() -> Dict[str, Any]:
        """Get thank you letter templates by donation type and amount"""
        return {
            'first_time': {
                'opening': [
                    "Welcome to our community of changemakers!",
                    "Your first gift marks the beginning of something special.",
                    "We're honored that you chose to make your first contribution to our cause."
                ],
                'impact': [
                    "Your support will immediately be put to work {specific_use}.",
                    "This contribution enables us to {primary_program} for those who need it most.",
                    "Thanks to you, we can continue {mission_action} in our community."
                ],
                'closing': [
                    "We look forward to sharing our impact journey with you.",
                    "Together, we'll make a lasting difference.",
                    "Welcome to our family of supporters."
                ]
            },
            'recurring': {
                'opening': [
                    "Your continued support means the world to us.",
                    "Once again, your generosity shines through.",
                    "Thank you for your ongoing commitment to our mission."
                ],
                'impact': [
                    "Your consistent support provides the stability we need to plan ahead.",
                    "Regular donors like you are the backbone of our organization.",
                    "Your sustained giving creates lasting change."
                ],
                'closing': [
                    "We're grateful for your continued partnership.",
                    "Thank you for standing with us.",
                    "Your loyalty inspires our work every day."
                ]
            },
            'major_gift': {
                'opening': [
                    "Your extraordinary generosity leaves us deeply moved.",
                    "We are profoundly grateful for your transformational gift.",
                    "Your remarkable contribution will create waves of positive change."
                ],
                'impact': [
                    "This significant investment will expand our {primary_program} to reach {expansion_metric} more individuals.",
                    "Your gift represents a game-changing moment for our organization and those we serve.",
                    "This level of support enables us to dream bigger and achieve more than we imagined possible."
                ],
                'closing': [
                    "We are honored to partner with you in this important work.",
                    "Your trust and investment in our mission humble and inspire us.",
                    "Thank you for being a catalyst for change."
                ]
            }
        }
    
    @staticmethod
    def get_grant_pitch_frameworks() -> Dict[str, Any]:
        """Get proven grant pitch structures"""
        return {
            'problem_solution': {
                'structure': [
                    "problem_statement",
                    "our_solution",
                    "proven_impact",
                    "funding_need",
                    "expected_outcomes"
                ],
                'components': {
                    'problem_statement': "In {service_area}, {problem_statistic} face {primary_challenge}.",
                    'our_solution': "{org_name} addresses this through {primary_programs}.",
                    'proven_impact': "Last year alone, we {key_achievement} with a {success_rate}% success rate.",
                    'funding_need': "With ${amount}, we will {specific_goal}.",
                    'expected_outcomes': "This investment will enable us to {expansion_plan}, impacting {beneficiary_projection} lives."
                }
            },
            'track_record': {
                'structure': [
                    "credibility",
                    "current_impact",
                    "opportunity",
                    "funding_request",
                    "roi"
                ],
                'components': {
                    'credibility': "For {years_active} years, {org_name} has been the leading {org_type} in {service_area}.",
                    'current_impact': "We currently serve {beneficiary_count} {beneficiaries} through {program_count} programs.",
                    'opportunity': "We've identified an opportunity to {growth_opportunity}.",
                    'funding_request': "A ${amount} investment will {specific_use}.",
                    'roi': "Every dollar invested returns {impact_multiplier} in community benefit."
                }
            },
            'alignment_focused': {
                'structure': [
                    "shared_values",
                    "aligned_goals",
                    "collaborative_approach",
                    "funding_synergy",
                    "partnership_vision"
                ],
                'components': {
                    'shared_values': "Like {funder_name}, we believe in {shared_value}.",
                    'aligned_goals': "Your priority of {funder_priority} perfectly aligns with our {matching_program}.",
                    'collaborative_approach': "Together, we can {collaborative_goal}.",
                    'funding_synergy': "${amount} from {funder_name} will catalyze {multiplier_effect}.",
                    'partnership_vision': "This partnership will establish {long_term_vision}."
                }
            }
        }
    
    @staticmethod
    def get_social_media_templates() -> Dict[str, List[str]]:
        """Get platform-specific social media templates"""
        return {
            'twitter': {
                'impact': [
                    "📊 {impact_number} lives changed this month! Thank you for making this possible. {cta} {hashtags}",
                    "🎯 GOAL REACHED: {achievement}! Your support made the difference. {cta} {hashtags}",
                    "✨ Real change happening: {specific_story}. Join us: {cta} {hashtags}"
                ],
                'fundraising': [
                    "📢 We're ${amount_needed} away from {goal}. Every dollar counts! {cta} {hashtags}",
                    "🚀 Help us reach our ${campaign_goal} goal by {deadline}! {progress}% there! {cta} {hashtags}",
                    "💪 Together we can {mission_verb}. Support our {campaign_name}: {cta} {hashtags}"
                ],
                'awareness': [
                    "Did you know? {statistic}. We're working to change this. Learn more: {cta} {hashtags}",
                    "📚 {educational_fact}. That's why our work matters. {cta} {hashtags}",
                    "🌟 Spotlight: {program_highlight}. See the impact: {cta} {hashtags}"
                ],
                'gratitude': [
                    "🙏 Thank you {donor_group} for {specific_support}! You make our work possible. {hashtags}",
                    "❤️ Grateful for our community! This week you helped us {achievement}. {hashtags}",
                    "🎉 Because of YOU: {impact_metric}. Thank you for believing in our mission! {hashtags}"
                ]
            },
            'linkedin': {
                'thought_leadership': [
                    """🔍 Insights from the Field: {topic_title}

At {org_name}, we've discovered that {key_insight}.

Key findings:
• {finding_1}
• {finding_2}
• {finding_3}

{call_to_discussion}

{hashtags}""",
                    """📈 Impact Report: {quarter} Highlights

This quarter, {org_name} achieved:
✓ {achievement_1}
✓ {achievement_2}
✓ {achievement_3}

{reflection_statement}

Read our full report: {cta}

{hashtags}"""
                ],
                'partnership': [
                    """🤝 Partnership Announcement

We're thrilled to partner with {partner_name} to {partnership_goal}.

This collaboration will:
• {benefit_1}
• {benefit_2}
• {benefit_3}

{closing_statement}

{hashtags}"""
                ]
            },
            'instagram': {
                'story': [
                    """✨ Meet {beneficiary_name} (privacy protected)

{brief_story}

Thanks to supporters like you, {positive_outcome}.

Swipe up to make more stories like this possible! 

{hashtags}""",
                    """📸 Behind the Scenes: {program_name}

Today our team {activity_description}.

Impact: {impact_metric}

Your support makes days like this possible! 💕

{hashtags}"""
                ]
            }
        }
    
    @staticmethod
    def get_newsletter_sections() -> Dict[str, Any]:
        """Get newsletter section templates"""
        return {
            'headers': {
                'seasonal': {
                    'spring': "🌸 Spring into Action: {month} Updates from {org_name}",
                    'summer': "☀️ Summer Impact Report: Making Waves in {month}",
                    'fall': "🍂 Fall Newsletter: Harvesting Change Together",
                    'winter': "❄️ Winter Updates: Warming Hearts in {month}"
                },
                'impact_focused': "{month} Impact: {key_metric} Lives Changed",
                'campaign': "Special Edition: {campaign_name} Campaign Update"
            },
            'opening_messages': [
                "Dear {subscriber_name|Friend}, As we reflect on {time_period}, we're filled with gratitude for your continued support.",
                "Greetings {subscriber_name|Supporter}, This month brought incredible moments of impact we're excited to share.",
                "Hello {subscriber_name|Champion}, Your support continues to create ripples of positive change."
            ],
            'sections': {
                'impact_highlight': {
                    'title': "Impact Spotlight",
                    'template': """This {time_period}, we achieved something remarkable:

{primary_achievement}

By the numbers:
• {metric_1}
• {metric_2}
• {metric_3}

{impact_story}"""
                },
                'program_update': {
                    'title': "Program Updates",
                    'template': """{program_name} Update:

{program_progress}

Recent milestones:
• {milestone_1}
• {milestone_2}

Coming next: {upcoming_activity}"""
                },
                'volunteer_spotlight': {
                    'title': "Volunteer of the Month",
                    'template': """We're honored to recognize {volunteer_name} for their outstanding dedication to {specific_contribution}.

{volunteer_quote}

Want to join our volunteer team? {volunteer_cta}"""
                },
                'upcoming_events': {
                    'title': "Save the Date",
                    'template': """Mark your calendars for these upcoming opportunities to get involved:

📅 {event_1_date}: {event_1_name}
   {event_1_description}

📅 {event_2_date}: {event_2_name}
   {event_2_description}

Register at {registration_link}"""
                },
                'donor_recognition': {
                    'title': "Thank You to Our Supporters",
                    'template': """We're grateful for the generosity of:

{donor_list}

Your contributions this month enabled us to {specific_impact}.

Join these champions: {donation_cta}"""
                },
                'call_to_action': {
                    'donate': "Support our mission with a gift of any size: {donation_link}",
                    'volunteer': "Join our volunteer team: {volunteer_link}",
                    'share': "Share our story with your network: {share_link}",
                    'event': "Register for {event_name}: {registration_link}"
                }
            },
            'closings': [
                "With gratitude and hope,\n{signatory_name}\n{signatory_title}",
                "Together in service,\n{signatory_name}\n{signatory_title}",
                "Thank you for being part of our journey,\n{signatory_name}\n{signatory_title}"
            ]
        }
    
    @staticmethod
    def get_impact_report_components() -> Dict[str, Any]:
        """Get impact report section templates"""
        return {
            'executive_summary': {
                'template': """EXECUTIVE SUMMARY

Reporting Period: {reporting_period}

{org_name} is pleased to present this impact report highlighting our achievements and the transformative difference your support has made in our community.

Key Achievements:
• {achievement_1}
• {achievement_2}
• {achievement_3}

Total Lives Impacted: {total_beneficiaries}
Programs Delivered: {program_count}
Success Rate: {success_percentage}%

{summary_statement}"""
            },
            'program_outcomes': {
                'template': """PROGRAM OUTCOMES

{program_name}:
• Participants Served: {participant_count}
• Completion Rate: {completion_rate}%
• Key Outcome: {primary_outcome}

Success Story:
{success_story}

Challenges and Solutions:
{challenge}: {solution}

Next Quarter Goals:
{future_goals}"""
            },
            'financial_summary': {
                'template': """FINANCIAL HIGHLIGHTS

Revenue Sources:
• Individual Donations: {individual_percentage}%
• Grants: {grants_percentage}%
• Events: {events_percentage}%
• Other: {other_percentage}%

Program Expense Ratio: {program_ratio}%

Every ${amount} donated created {impact_per_dollar} in community value."""
            },
            'testimonials': {
                'participant': "\"{testimonial_text}\" - {participant_identifier}, Program Participant",
                'volunteer': "\"{testimonial_text}\" - {volunteer_name}, Volunteer",
                'partner': "\"{testimonial_text}\" - {partner_name}, Community Partner"
            },
            'looking_ahead': {
                'template': """LOOKING AHEAD

Building on this quarter's success, we are:

1. {future_initiative_1}
2. {future_initiative_2}
3. {future_initiative_3}

With your continued support, we project to {future_impact_projection} in the coming quarter.

{closing_inspiration}"""
            }
        }
    
    @staticmethod
    def get_metrics_templates() -> Dict[str, str]:
        """Get templates for presenting metrics and data"""
        return {
            'single_metric': "{value} {unit} {action}",
            'comparison': "{current_value} {unit}, a {percentage}% increase from {previous_value}",
            'milestone': "Reached {milestone_value} {milestone_unit} for the first time",
            'projection': "On track to {action} {projected_value} {unit} by {target_date}",
            'percentage': "{percentage}% of {population} {action}",
            'ratio': "For every {input_value}, we {output_action} {output_value}",
            'time_saved': "Saved {hours} hours of {activity}, equivalent to ${dollar_value}",
            'cost_per': "Achieved {outcome} at just ${cost} per {unit}",
            'growth': "Grew {metric} by {percentage}% year-over-year",
            'reach': "Extended our reach to {new_number} new {beneficiary_type}"
        }