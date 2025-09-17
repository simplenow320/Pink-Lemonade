"""
Website Context Service
Extracts meaningful organizational context from websites for AI writing
"""

import logging
import re
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from app import db
from app.models import Organization
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

class WebsiteContextService:
    """
    Extracts deep organizational context from websites to enable AI to write
    with intimate knowledge of the organization's voice, programs, and impact.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (GrantFlow Pro Context Analyzer)'
        })
        self.cache = {}
        self.cache_duration = timedelta(days=7)
    
    def fetch_website_context(self, website_url: str, org_id: Optional[int] = None) -> Dict:
        """
        Main method to fetch and extract comprehensive context from a website.
        Returns structured data about the organization for AI consumption.
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(website_url)
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if cached_data['cached_at'] > datetime.utcnow() - self.cache_duration:
                    logger.info(f"Using cached context for {website_url}")
                    return cached_data['context']
            
            # Normalize URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            # Parse base URL
            parsed_url = urlparse(website_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Fetch main page
            logger.info(f"Fetching website context from {website_url}")
            response = self.session.get(website_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract various context elements
            context = {
                'website_url': website_url,
                'fetched_at': datetime.utcnow().isoformat(),
                'organization_voice': self._extract_voice_and_tone(soup),
                'mission_vision': self._extract_mission_vision(soup),
                'about_content': self._extract_about_content(soup),
                'programs': self._extract_programs(soup),
                'team_leadership': self._extract_team_info(soup),
                'impact_stories': self._extract_impact_stories(soup),
                'news_updates': self._extract_news_updates(soup, base_url),
                'testimonials': self._extract_testimonials(soup),
                'partners_funders': self._extract_partners(soup),
                'contact_info': self._extract_contact_info(soup),
                'social_media': self._extract_social_media(soup),
                'key_statistics': self._extract_statistics(soup),
                'unique_value_props': self._extract_value_propositions(soup),
                'awards_recognition': self._extract_awards(soup),
                'media_mentions': self._extract_media_mentions(soup),
                'donation_language': self._extract_donation_language(soup),
                'calls_to_action': self._extract_ctas(soup),
                'meta_description': self._extract_meta_description(soup),
                'keywords': self._extract_keywords(soup)
            }
            
            # Fetch additional pages for more context
            context['additional_pages'] = self._fetch_key_pages(soup, base_url)
            
            # Generate summary and insights
            context['summary'] = self._generate_context_summary(context)
            context['writing_guidelines'] = self._generate_writing_guidelines(context)
            
            # Cache the result
            self.cache[cache_key] = {
                'context': context,
                'cached_at': datetime.utcnow()
            }
            
            # Optionally save to database
            if org_id:
                self._save_to_database(org_id, context)
            
            return context
            
        except requests.RequestException as e:
            logger.error(f"Error fetching website {website_url}: {e}")
            return self._get_fallback_context(website_url)
        except Exception as e:
            logger.error(f"Unexpected error processing website {website_url}: {e}")
            return self._get_fallback_context(website_url)
    
    def _extract_voice_and_tone(self, soup: BeautifulSoup) -> Dict:
        """Extract the organization's voice and tone from their content"""
        voice_analysis = {
            'tone': 'professional',
            'style': 'informative',
            'formality': 'formal',
            'emotion': 'passionate',
            'key_phrases': []
        }
        
        # Analyze headers and main content
        headers = soup.find_all(['h1', 'h2', 'h3'])
        content_blocks = soup.find_all(['p', 'div'], class_=re.compile('content|about|mission'))
        
        all_text = ' '.join([elem.get_text() for elem in headers + content_blocks[:10]])
        
        # Detect tone indicators
        if re.search(r'\b(transform|revolutionize|disrupt|innovate)\b', all_text, re.I):
            voice_analysis['tone'] = 'innovative'
        elif re.search(r'\b(compassion|care|heart|love|support)\b', all_text, re.I):
            voice_analysis['tone'] = 'compassionate'
        elif re.search(r'\b(empower|enable|uplift|strengthen)\b', all_text, re.I):
            voice_analysis['tone'] = 'empowering'
        
        # Detect formality
        if re.search(r'\b(we\'re|you\'re|let\'s|won\'t)\b', all_text):
            voice_analysis['formality'] = 'conversational'
        elif re.search(r'\b(shall|therefore|pursuant|whereas)\b', all_text):
            voice_analysis['formality'] = 'very formal'
        
        # Extract key phrases (organization's language patterns)
        sentences = all_text.split('.')[:20]
        for sentence in sentences:
            if len(sentence) < 100 and len(sentence) > 20:
                if re.search(r'\b(mission|vision|believe|committed|dedicated)\b', sentence, re.I):
                    voice_analysis['key_phrases'].append(sentence.strip())
        
        return voice_analysis
    
    def _extract_mission_vision(self, soup: BeautifulSoup) -> Dict:
        """Extract mission and vision statements"""
        mission_vision = {
            'mission': '',
            'vision': '',
            'values': [],
            'tagline': ''
        }
        
        # Look for mission statement
        mission_patterns = ['mission', 'our-mission', 'about-us']
        for pattern in mission_patterns:
            mission_elem = soup.find(['div', 'section', 'p'], class_=re.compile(pattern, re.I))
            if not mission_elem:
                mission_elem = soup.find(['h1', 'h2', 'h3'], text=re.compile('mission', re.I))
                if mission_elem:
                    mission_elem = mission_elem.find_next_sibling(['p', 'div'])
            
            if mission_elem:
                mission_vision['mission'] = mission_elem.get_text(strip=True)[:500]
                break
        
        # Look for vision statement
        vision_elem = soup.find(['div', 'section', 'p'], class_=re.compile('vision', re.I))
        if vision_elem:
            mission_vision['vision'] = vision_elem.get_text(strip=True)[:500]
        
        # Look for values
        values_section = soup.find(['div', 'section', 'ul'], class_=re.compile('values', re.I))
        if values_section and isinstance(values_section, Tag):
            values_items = values_section.find_all(['li', 'p'])[:10]
            mission_vision['values'] = [item.get_text(strip=True)[:100] for item in values_items]
        
        # Look for tagline
        tagline_elem = soup.find(['h1', 'h2', 'p'], class_=re.compile('tagline|slogan|motto', re.I))
        if tagline_elem:
            mission_vision['tagline'] = tagline_elem.get_text(strip=True)[:150]
        
        return mission_vision
    
    def _extract_about_content(self, soup: BeautifulSoup) -> Dict:
        """Extract About Us content"""
        about_content = {
            'overview': '',
            'history': '',
            'approach': '',
            'why_we_exist': ''
        }
        
        # Find About section
        about_section = soup.find(['div', 'section'], class_=re.compile('about', re.I))
        if about_section and isinstance(about_section, Tag):
            paragraphs = about_section.find_all('p')[:5]
            about_content['overview'] = ' '.join([p.get_text(strip=True) for p in paragraphs])[:1000]
        
        # Look for history
        history_elem = soup.find(['div', 'section'], class_=re.compile('history|story|founded', re.I))
        if history_elem:
            about_content['history'] = history_elem.get_text(strip=True)[:500]
        
        # Look for approach/methodology
        approach_elem = soup.find(['div', 'section'], class_=re.compile('approach|how-we-work|methodology', re.I))
        if approach_elem:
            about_content['approach'] = approach_elem.get_text(strip=True)[:500]
        
        return about_content
    
    def _extract_programs(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract program information"""
        programs = []
        
        # Look for programs section
        program_sections = soup.find_all(['div', 'section'], class_=re.compile('program|service|initiative|project', re.I))[:10]
        
        for section in program_sections:
            program = {}
            
            # Get program name
            if isinstance(section, Tag):
                title = section.find(['h2', 'h3', 'h4'])
                if title and isinstance(title, Tag):
                    program['name'] = title.get_text(strip=True)
            
            # Get description
            if isinstance(section, Tag):
                desc = section.find(['p', 'div'], class_=re.compile('desc|summary|overview', re.I))
                if desc and isinstance(desc, Tag):
                    program['description'] = desc.get_text(strip=True)[:300]
                else:
                    p_elem = section.find('p')
                    if p_elem and isinstance(p_elem, Tag):
                        program['description'] = p_elem.get_text(strip=True)[:300]
            
            # Get impact/outcomes
            if isinstance(section, Tag):
                impact = section.find(['p', 'div', 'ul'], class_=re.compile('impact|outcome|result', re.I))
                if impact and isinstance(impact, Tag):
                    program['impact'] = impact.get_text(strip=True)[:200]
            
            if program:
                programs.append(program)
        
        return programs
    
    def _extract_team_info(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract team and leadership information"""
        team = []
        
        # Look for team section
        team_sections = soup.find_all(['div', 'section'], class_=re.compile('team|staff|leadership|board', re.I))[:5]
        
        for section in team_sections:
            if not isinstance(section, Tag):
                continue
            members = section.find_all(['div', 'article'], class_=re.compile('member|person|profile', re.I))[:20]
            
            for member in members:
                if not isinstance(member, Tag):
                    continue
                person = {}
                
                # Get name
                name_elem = member.find(['h3', 'h4', 'h5', 'strong'])
                if name_elem and isinstance(name_elem, Tag):
                    person['name'] = name_elem.get_text(strip=True)
                
                # Get title/role
                title_elem = member.find(['p', 'span'], class_=re.compile('title|role|position', re.I))
                if title_elem and isinstance(title_elem, Tag):
                    person['title'] = title_elem.get_text(strip=True)
                
                # Get bio
                bio_elem = member.find(['p', 'div'], class_=re.compile('bio|description', re.I))
                if bio_elem and isinstance(bio_elem, Tag):
                    person['bio'] = bio_elem.get_text(strip=True)[:200]
                
                if person and 'name' in person:
                    team.append(person)
        
        return team[:15]  # Limit to top 15 team members
    
    def _extract_impact_stories(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract impact stories and case studies"""
        stories = []
        
        # Look for impact/success stories
        story_sections = soup.find_all(['div', 'article', 'section'], 
                                      class_=re.compile('impact|success|story|case-study|testimonial', re.I))[:10]
        
        for section in story_sections:
            if not isinstance(section, Tag):
                continue
            story = {}
            
            # Get title
            title = section.find(['h2', 'h3', 'h4'])
            if title and isinstance(title, Tag):
                story['title'] = title.get_text(strip=True)
            
            # Get content
            content = section.find(['p', 'div'], class_=re.compile('content|story|description', re.I))
            if content and isinstance(content, Tag):
                story['content'] = content.get_text(strip=True)[:500]
            elif isinstance(section, Tag):
                p_elems = section.find_all('p')[:3]
                if p_elems:
                    story['content'] = ' '.join([p.get_text(strip=True) for p in p_elems if isinstance(p, Tag)])[:500]
            
            # Look for metrics/numbers
            numbers = re.findall(r'\b(\d+[,\d]*)\s*(people|families|children|students|clients|participants|volunteers|%)', 
                                section.get_text(), re.I)
            if numbers:
                story['metrics'] = [f"{num[0]} {num[1]}" for num in numbers[:5]]
            
            if story and ('content' in story or 'metrics' in story):
                stories.append(story)
        
        return stories
    
    def _extract_news_updates(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract recent news and blog posts"""
        news = []
        
        # Look for news/blog section
        news_sections = soup.find_all(['div', 'section', 'article'], 
                                     class_=re.compile('news|blog|update|announcement|press', re.I))[:10]
        
        for section in news_sections:
            if not isinstance(section, Tag):
                continue
            article = {}
            
            # Get title
            title = section.find(['h2', 'h3', 'h4', 'a'])
            if title and isinstance(title, Tag):
                article['title'] = title.get_text(strip=True)
                
                # Get link if available
                if title.name == 'a':
                    href = title.get('href')
                    if href:
                        article['link'] = urljoin(base_url, str(href))
            
            # Get date
            date_elem = section.find(['time', 'span', 'p'], class_=re.compile('date|time|published', re.I))
            if date_elem and isinstance(date_elem, Tag):
                article['date'] = date_elem.get_text(strip=True)
            
            # Get excerpt
            excerpt = section.find(['p', 'div'], class_=re.compile('excerpt|summary|description', re.I))
            if excerpt and isinstance(excerpt, Tag):
                article['excerpt'] = excerpt.get_text(strip=True)[:300]
            
            if article:
                news.append(article)
        
        return news[:5]  # Return top 5 news items
    
    def _extract_testimonials(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract testimonials and quotes"""
        testimonials = []
        
        # Look for testimonial sections
        testimonial_sections = soup.find_all(['div', 'blockquote', 'section'], 
                                            class_=re.compile('testimonial|quote|review|feedback', re.I))[:10]
        
        for section in testimonial_sections:
            if not isinstance(section, Tag):
                continue
            testimonial = {}
            
            # Get quote text
            quote = section.find(['p', 'blockquote', 'q'])
            if quote and isinstance(quote, Tag):
                testimonial['quote'] = quote.get_text(strip=True)[:400]
            
            # Get author
            author = section.find(['cite', 'span', 'p'], class_=re.compile('author|name|source|attribution', re.I))
            if author and isinstance(author, Tag):
                testimonial['author'] = author.get_text(strip=True)
            
            if testimonial and 'quote' in testimonial:
                testimonials.append(testimonial)
        
        return testimonials
    
    def _extract_partners(self, soup: BeautifulSoup) -> Dict:
        """Extract partners and funders information"""
        partners = {
            'funders': [],
            'partners': [],
            'supporters': []
        }
        
        # Look for partner/funder sections
        partner_sections = soup.find_all(['div', 'section'], 
                                        class_=re.compile('partner|funder|supporter|sponsor|donor', re.I))
        
        for section in partner_sections:
            if not isinstance(section, Tag):
                continue
            # Look for lists of partners
            partner_lists = section.find_all(['ul', 'div'], class_=re.compile('list|grid|logos', re.I))
            
            for plist in partner_lists:
                if not isinstance(plist, Tag):
                    continue
                items = plist.find_all(['li', 'img', 'a'])[:20]
                
                for item in items:
                    if not isinstance(item, Tag):
                        continue
                    name = ''
                    if item.name == 'img':
                        alt_text = item.get('alt')
                        if alt_text:
                            name = str(alt_text)
                    elif hasattr(item, 'get_text'):
                        name = item.get_text(strip=True)
                    
                    if name and len(name) < 100:
                        section_classes = section.get('class') if isinstance(section, Tag) else []
                        section_text = section.get_text().lower() if isinstance(section, Tag) else ''
                        if isinstance(section_classes, list):
                            section_classes_str = ' '.join(section_classes)
                        elif section_classes:
                            section_classes_str = str(section_classes)
                        else:
                            section_classes_str = ''
                        
                        if 'funder' in section_classes_str or 'funder' in section_text:
                            partners['funders'].append(name)
                        elif 'partner' in section_classes_str or 'partner' in section_text:
                            partners['partners'].append(name)
                        else:
                            partners['supporters'].append(name)
        
        # Limit lists
        partners['funders'] = list(set(partners['funders']))[:15]
        partners['partners'] = list(set(partners['partners']))[:15]
        partners['supporters'] = list(set(partners['supporters']))[:10]
        
        return partners
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Extract contact information"""
        contact = {
            'email': '',
            'phone': '',
            'address': '',
            'contact_page': ''
        }
        
        # Look for email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            contact['email'] = emails[0]
        
        # Look for phone
        phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}'
        phones = re.findall(phone_pattern, soup.get_text())
        if phones:
            contact['phone'] = phones[0]
        
        # Look for address
        address_elem = soup.find(['address', 'div', 'p'], class_=re.compile('address|location', re.I))
        if address_elem:
            contact['address'] = address_elem.get_text(strip=True)[:200]
        
        # Look for contact page link
        contact_link = soup.find('a', text=re.compile('contact', re.I))
        if contact_link and isinstance(contact_link, Tag):
            href = contact_link.get('href')
            if href:
                contact['contact_page'] = str(href)
        
        return contact
    
    def _extract_social_media(self, soup: BeautifulSoup) -> Dict:
        """Extract social media links"""
        social = {}
        
        platforms = ['facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'tiktok']
        
        for platform in platforms:
            link = soup.find('a', href=re.compile(platform, re.I))
            if link and isinstance(link, Tag):
                href = link.get('href')
                if href:
                    social[platform] = str(href)
        
        return social
    
    def _extract_statistics(self, soup: BeautifulSoup) -> List[str]:
        """Extract key statistics and numbers"""
        stats = []
        
        # Look for statistics sections
        stat_sections = soup.find_all(['div', 'section'], 
                                     class_=re.compile('stat|number|metric|impact|achievement', re.I))
        
        for section in stat_sections:
            # Find numbers with context
            text = section.get_text()
            
            # Match patterns like "500+ families served", "95% success rate"
            stat_patterns = [
                r'(\d+[,\d]*\+?)\s+([\w\s]{2,20})',
                r'(\d+%)\s+([\w\s]{2,20})',
                r'([\$]\d+[,\d]*[MKB]?)\s+([\w\s]{2,20})'
            ]
            
            for pattern in stat_patterns:
                matches = re.findall(pattern, text)
                for match in matches[:10]:
                    stat_text = f"{match[0]} {match[1]}"
                    if stat_text not in stats:
                        stats.append(stat_text)
        
        return stats[:20]
    
    def _extract_value_propositions(self, soup: BeautifulSoup) -> List[str]:
        """Extract unique value propositions"""
        values = []
        
        # Look for why choose us / what makes us different sections
        value_sections = soup.find_all(['div', 'section'], 
                                      class_=re.compile('why|unique|different|advantage|benefit', re.I))
        
        for section in value_sections:
            if not isinstance(section, Tag):
                continue
            # Get list items or paragraphs
            items = section.find_all(['li', 'p'])[:10]
            for item in items:
                text = item.get_text(strip=True)
                if 20 < len(text) < 200:
                    values.append(text)
        
        return values[:10]
    
    def _extract_awards(self, soup: BeautifulSoup) -> List[str]:
        """Extract awards and recognition"""
        awards = []
        
        # Look for awards sections
        award_sections = soup.find_all(['div', 'section'], 
                                      class_=re.compile('award|recognition|achievement|honor|accreditation', re.I))
        
        for section in award_sections:
            if not isinstance(section, Tag):
                continue
            items = section.find_all(['li', 'p', 'h3', 'h4'])[:10]
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) < 150:
                    awards.append(text)
        
        return awards[:10]
    
    def _extract_media_mentions(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract media mentions and press coverage"""
        mentions = []
        
        # Look for press/media sections
        media_sections = soup.find_all(['div', 'section'], 
                                      class_=re.compile('press|media|news|coverage|featured', re.I))
        
        for section in media_sections:
            if not isinstance(section, Tag):
                continue
            items = section.find_all(['li', 'div', 'article'])[:10]
            
            for item in items:
                if not isinstance(item, Tag):
                    continue
                mention = {}
                
                # Get outlet name
                outlet = item.find(['strong', 'b', 'h4'])
                if outlet and isinstance(outlet, Tag):
                    mention['outlet'] = outlet.get_text(strip=True)
                
                # Get title/description
                title = item.find(['a', 'p'])
                if title and isinstance(title, Tag):
                    mention['title'] = title.get_text(strip=True)[:200]
                
                if mention:
                    mentions.append(mention)
        
        return mentions[:10]
    
    def _extract_donation_language(self, soup: BeautifulSoup) -> Dict:
        """Extract how the organization talks about donations"""
        donation = {
            'call_to_action': '',
            'impact_levels': [],
            'recurring_ask': '',
            'urgency_language': ''
        }
        
        # Find donation sections
        donation_sections = soup.find_all(['div', 'section'], 
                                         class_=re.compile('donat|give|support|contribute|help', re.I))
        
        for section in donation_sections[:3]:
            if not isinstance(section, Tag):
                continue
            text = section.get_text()
            
            # Get main CTA
            if not donation['call_to_action']:
                cta = section.find(['button', 'a'], text=re.compile('donate|give|support', re.I))
                if cta and isinstance(cta, Tag):
                    donation['call_to_action'] = cta.get_text(strip=True)
            
            # Look for impact levels ($25 provides...)
            impact_matches = re.findall(r'[\$](\d+)\s+(?:provides?|helps?|supports?|funds?|covers?|enables?)([^.!?]{10,100})', text, re.I)
            for match in impact_matches[:5]:
                donation['impact_levels'].append(f"${match[0]} {match[1]}")
            
            # Look for recurring language
            if re.search(r'monthly|recurring|sustaining|ongoing', text, re.I):
                sentences = text.split('.')
                for sentence in sentences:
                    if re.search(r'monthly|recurring|sustaining', sentence, re.I):
                        donation['recurring_ask'] = sentence.strip()[:200]
                        break
            
            # Look for urgency
            if re.search(r'now|today|urgent|immediate|critical', text, re.I):
                sentences = text.split('.')
                for sentence in sentences:
                    if re.search(r'now|today|urgent|immediate|critical', sentence, re.I):
                        donation['urgency_language'] = sentence.strip()[:200]
                        break
        
        return donation
    
    def _extract_ctas(self, soup: BeautifulSoup) -> List[str]:
        """Extract various calls to action"""
        ctas = []
        
        # Find all CTA buttons and links
        cta_elements = soup.find_all(['button', 'a'], 
                                    class_=re.compile('cta|button|btn|action', re.I))[:20]
        
        for elem in cta_elements:
            text = elem.get_text(strip=True)
            if text and len(text) < 50 and text not in ctas:
                ctas.append(text)
        
        return ctas[:10]
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description for SEO understanding"""
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta and isinstance(meta, Tag):
            content = meta.get('content')
            if content:
                return str(content)[:300]
        return ''
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from meta tags and content"""
        keywords = []
        
        # Get meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and isinstance(meta_keywords, Tag):
            content = meta_keywords.get('content')
            if content:
                keywords.extend(str(content).split(',')[:10])
        
        # Extract frequent important words from headers
        headers = soup.find_all(['h1', 'h2', 'h3'])[:20]
        header_text = ' '.join([h.get_text() for h in headers])
        
        # Find capitalized multi-word phrases (likely important)
        important_phrases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', header_text)
        keywords.extend(important_phrases[:10])
        
        return list(set([k.strip() for k in keywords if k.strip()]))[:20]
    
    def _fetch_key_pages(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """Fetch additional key pages for more context"""
        key_pages = {}
        
        # Define pages to look for
        target_pages = ['about', 'programs', 'impact', 'team', 'mission']
        
        for page_type in target_pages:
            # Find link to this page
            link = soup.find('a', href=re.compile(f'/{page_type}', re.I))
            if link and isinstance(link, Tag):
                href = link.get('href')
                if href:
                    try:
                        page_url = urljoin(base_url, str(href))
                        response = self.session.get(page_url, timeout=5)
                        if response.status_code == 200:
                            page_soup = BeautifulSoup(response.content, 'html.parser')
                            # Get main content
                            main = page_soup.find(['main', 'div'], class_=re.compile('content|main', re.I))
                            if main and isinstance(main, Tag):
                                # Get first few paragraphs
                                paragraphs = main.find_all('p')[:5]
                                key_pages[page_type] = ' '.join([p.get_text(strip=True) for p in paragraphs if isinstance(p, Tag)])[:1000]
                    except:
                        continue
        
        return key_pages
    
    def _generate_context_summary(self, context: Dict) -> str:
        """Generate a comprehensive summary of the organization"""
        summary_parts = []
        
        # Add mission
        if context['mission_vision'].get('mission'):
            summary_parts.append(f"Mission: {context['mission_vision']['mission'][:200]}")
        
        # Add tagline
        if context['mission_vision'].get('tagline'):
            summary_parts.append(f"Tagline: {context['mission_vision']['tagline']}")
        
        # Add key programs
        if context['programs']:
            program_names = [p['name'] for p in context['programs'][:3] if 'name' in p]
            if program_names:
                summary_parts.append(f"Key Programs: {', '.join(program_names)}")
        
        # Add impact stats
        if context['key_statistics']:
            summary_parts.append(f"Impact: {', '.join(context['key_statistics'][:3])}")
        
        # Add unique value props
        if context['unique_value_props']:
            summary_parts.append(f"Unique Value: {context['unique_value_props'][0][:200]}")
        
        # Add recent achievement
        if context['awards_recognition']:
            summary_parts.append(f"Recognition: {context['awards_recognition'][0][:100]}")
        
        return ' | '.join(summary_parts)
    
    def _generate_writing_guidelines(self, context: Dict) -> Dict:
        """Generate AI writing guidelines based on website analysis"""
        guidelines = {
            'tone': context['organization_voice']['tone'],
            'formality': context['organization_voice']['formality'],
            'key_messaging': [],
            'words_to_use': [],
            'words_to_avoid': [],
            'proof_points': []
        }
        
        # Extract key messaging from tagline and mission
        if context['mission_vision']['tagline']:
            guidelines['key_messaging'].append(context['mission_vision']['tagline'])
        
        if context['organization_voice']['key_phrases']:
            guidelines['key_messaging'].extend(context['organization_voice']['key_phrases'][:3])
        
        # Determine words to use based on content
        all_text = ' '.join([
            context.get('summary', ''),
            context['mission_vision'].get('mission', ''),
            context['about_content'].get('overview', '')
        ])
        
        # Extract frequently used important words
        important_words = re.findall(r'\b(transform|empower|impact|community|support|enable|change|help|serve|provide)\w*\b', 
                                    all_text, re.I)
        word_freq = {}
        for word in important_words:
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # Get top used words
        guidelines['words_to_use'] = sorted(word_freq.keys(), key=lambda x: word_freq.get(x, 0), reverse=True)[:10]
        
        # Set words to avoid based on tone
        if context['organization_voice']['tone'] == 'compassionate':
            guidelines['words_to_avoid'] = ['aggressive', 'dominate', 'crush', 'destroy']
        elif context['organization_voice']['tone'] == 'professional':
            guidelines['words_to_avoid'] = ['awesome', 'cool', 'stuff', 'thing']
        
        # Add proof points from impact and testimonials
        if context['key_statistics']:
            guidelines['proof_points'].extend(context['key_statistics'][:5])
        
        if context['awards_recognition']:
            guidelines['proof_points'].extend(context['awards_recognition'][:3])
        
        return guidelines
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _save_to_database(self, org_id: int, context: Dict):
        """Save website context to database for future use"""
        try:
            org = Organization.query.get(org_id)
            if org:
                # Store in website_context JSON field if it exists
                if hasattr(org, 'website_context'):
                    org.website_context = context
                    db.session.commit()
                    logger.info(f"Saved website context for org {org_id}")
        except Exception as e:
            logger.error(f"Error saving website context to database: {e}")
    
    def _get_fallback_context(self, website_url: str) -> Dict:
        """Return minimal context when website fetch fails"""
        return {
            'website_url': website_url,
            'error': 'Unable to fetch website content',
            'fetched_at': datetime.utcnow().isoformat(),
            'summary': f"Website: {website_url}",
            'writing_guidelines': {
                'tone': 'professional',
                'formality': 'formal',
                'key_messaging': [],
                'words_to_use': ['impact', 'community', 'support', 'mission'],
                'words_to_avoid': [],
                'proof_points': []
            }
        }