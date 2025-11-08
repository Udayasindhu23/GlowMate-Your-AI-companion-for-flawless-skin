import os
import re
from typing import Optional, List, Dict
import sqlite3
from difflib import SequenceMatcher

# Try to import OpenAI (optional dependency)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Initialize OpenAI client (will use environment variable)
# For production, set OPENAI_API_KEY environment variable
openai_client = None
if OPENAI_AVAILABLE:
    api_key = os.getenv('OPENAI_API_KEY', '')
    if api_key:
        openai_client = OpenAI(api_key=api_key)

# Conversation context storage (in-memory, session-based)
conversation_context = {}

def get_conversation_history(session_id: str, limit: int = 5) -> List[Dict]:
    """Get recent conversation history for context"""
    try:
        conn = sqlite3.connect('skincare.db')
        c = conn.cursor()
        c.execute('''
            SELECT message, response
            FROM chat_history
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (session_id, limit))
        
        history = []
        for row in c.fetchall():
            history.insert(0, {'user': row[0], 'bot': row[1]})
        
        conn.close()
        return history
    except:
        return []

def update_context(session_id: str, key: str, value: str):
    """Update conversation context"""
    if session_id not in conversation_context:
        conversation_context[session_id] = {}
    conversation_context[session_id][key] = value

def get_context(session_id: str, key: str, default=None):
    """Get conversation context"""
    return conversation_context.get(session_id, {}).get(key, default)

def similar(a: str, b: str) -> float:
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_skin_type(message: str) -> Optional[str]:
    """Extract skin type from message"""
    message_lower = message.lower()
    skin_types = {
        'oily': ['oily', 'greasy', 'shiny', 'oil'],
        'dry': ['dry', 'flaky', 'dehydrated', 'tight'],
        'combination': ['combination', 'combo', 'mixed', 't-zone'],
        'sensitive': ['sensitive', 'irritated', 'red', 'reactive'],
        'normal': ['normal', 'balanced', 'healthy']
    }
    
    for skin_type, keywords in skin_types.items():
        for keyword in keywords:
            if keyword in message_lower:
                return skin_type
    return None

def extract_concern(message: str) -> Optional[str]:
    """Extract skin concern from message"""
    message_lower = message.lower()
    concerns = {
        'acne': ['acne', 'pimple', 'breakout', 'blemish', 'zit', 'pustule'],
        'wrinkles': ['wrinkle', 'fine lines', 'aging', 'age', 'anti-aging'],
        'dark_circles': ['dark circles', 'under eye', 'eye bags', 'puffy eyes'],
        'dryness': ['dry', 'flaky', 'dehydrated', 'tight'],
        'oiliness': ['oily', 'greasy', 'shiny'],
        'redness': ['red', 'redness', 'irritation', 'inflamed'],
        'uneven_tone': ['uneven', 'pigmentation', 'dark spots', 'hyperpigmentation'],
        'sensitivity': ['sensitive', 'irritated', 'stinging', 'burning']
    }
    
    for concern, keywords in concerns.items():
        for keyword in keywords:
            if keyword in message_lower:
                return concern
    return None

def get_chatbot_response(message: str, session_id: str = None) -> str:
    """
    Get response from chatbot using OpenAI API or fallback to rule-based responses
    Enhanced with conversation context and better NLP
    """
    # Try OpenAI API if available and key is set
    if openai_client:
        try:
            return get_openai_response(message, session_id)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to rule-based
            return get_enhanced_rule_based_response(message, session_id)
    else:
        # Use enhanced rule-based responses
        return get_enhanced_rule_based_response(message, session_id)

def get_openai_response(message: str, session_id: str = None) -> str:
    """Get response using OpenAI GPT API with conversation context"""
    if not openai_client:
        raise Exception("OpenAI client not initialized")
    
    # Get conversation history
    history_messages = []
    if session_id:
        history = get_conversation_history(session_id, limit=5)
        for h in history:
            history_messages.append({"role": "user", "content": h['user']})
            history_messages.append({"role": "assistant", "content": h['bot']})
    
    # Build context
    context_info = ""
    if session_id:
        skin_type = get_context(session_id, 'skin_type')
        if skin_type:
            context_info = f"The user has {skin_type} skin type. "
    
    messages = [
        {
            "role": "system",
            "content": f"You are a helpful, knowledgeable skincare assistant. {context_info}Provide accurate, safe, and personalized skincare advice. Always recommend consulting a dermatologist for serious skin concerns. Be conversational and friendly."
        }
    ]
    
    messages.extend(history_messages)
    messages.append({"role": "user", "content": message})
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise e

def get_enhanced_rule_based_response(message: str, session_id: str = None) -> str:
    """
    Enhanced rule-based chatbot with better NLP, context awareness, and more topics
    """
    message_lower = message.lower().strip()
    original_message = message
    
    # Handle greetings
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
    if any(greeting in message_lower for greeting in greetings):
        skin_type = get_context(session_id, 'skin_type') if session_id else None
        if skin_type:
            return f"Hello! I remember you have {skin_type} skin. How can I help you with your skincare today? 😊"
        return "Hello! I'm your skincare assistant. I can help you with skincare routines, products, acne, skin types, and more! What would you like to know? 😊"
    
    # Handle thanks/goodbye
    if any(word in message_lower for word in ['thanks', 'thank you', 'bye', 'goodbye', 'see you']):
        return "You're welcome! Feel free to come back anytime if you have more skincare questions. Take care of your skin! 💙"
    
    # Extract and store skin type if mentioned
    skin_type = extract_skin_type(message)
    if skin_type and session_id:
        update_context(session_id, 'skin_type', skin_type)
    
    # Extract skin concern
    concern = extract_concern(message)
    
    # Get conversation history for context
    history = get_conversation_history(session_id, limit=3) if session_id else []
    previous_context = get_context(session_id, 'skin_type') if session_id else None
    
    # Enhanced topic matching with better NLP
    
    # 1. Acne-related (most specific first)
    acne_keywords = ['acne', 'pimple', 'breakout', 'blemish', 'zit', 'whitehead', 'blackhead', 'cystic acne']
    if any(keyword in message_lower for keyword in acne_keywords):
        responses = [
            f"For acne, I recommend:\n\n1. **Cleansing**: Use a salicylic acid cleanser twice daily\n2. **Treatment**: Apply benzoyl peroxide or salicylic acid spot treatment\n3. **Moisturizer**: Use oil-free, non-comedogenic moisturizer\n4. **Sunscreen**: Always use SPF 30+ (acne can worsen with sun exposure)\n5. **Avoid**: Don't pick or pop pimples, avoid touching your face\n\nIf acne persists after 6-8 weeks, consider seeing a dermatologist for prescription treatments.",
            f"Acne management tips:\n\n• Cleanse with salicylic acid (2% for mild, 5% for moderate)\n• Use benzoyl peroxide (2.5-5%) for active breakouts\n• Choose non-comedogenic products (won't clog pores)\n• Don't over-cleanse (2x daily max)\n• Change pillowcases regularly\n• Avoid harsh scrubs that can irritate\n• Consider seeing a dermatologist if OTC treatments don't work",
            f"To treat acne effectively:\n\n**Daily Routine:**\n- Morning: Gentle cleanser → Salicylic acid treatment → Oil-free moisturizer → Sunscreen\n- Night: Double cleanse → Benzoyl peroxide → Moisturizer\n\n**Lifestyle:**\n- Keep hair off your face\n- Clean phone screen regularly\n- Don't touch your face\n- Manage stress (can trigger breakouts)\n\nFor severe or persistent acne, consult a dermatologist for prescription options."
        ]
        return responses[0] if not previous_context else f"Since you have {previous_context} skin, here's acne advice: {responses[0]}"
    
    # 2. Exfoliation
    exfoliation_keywords = ['exfoliate', 'exfoliation', 'scrub', 'peel', 'aha', 'bha', 'glycolic', 'lactic acid']
    if any(keyword in message_lower for keyword in exfoliation_keywords):
        frequency = "2-3 times per week" if previous_context in ['oily', 'combination'] else "1-2 times per week" if previous_context == 'sensitive' else "2 times per week"
        return f"Exfoliation guidelines:\n\n**Frequency:**\n- {frequency} for most skin types\n- Start with once a week and increase gradually\n\n**Types:**\n- **Chemical exfoliants (AHAs/BHAs)**: Gentler, more effective\n  - AHAs (glycolic, lactic acid): Surface exfoliation, brightening\n  - BHAs (salicylic acid): Penetrate pores, great for acne\n- **Physical scrubs**: Can be too harsh, avoid for sensitive skin\n\n**Tips:**\n- Never exfoliate broken or irritated skin\n- Always use sunscreen (exfoliation increases sun sensitivity)\n- Moisturize well after exfoliating\n- Stop if you experience irritation"
    
    # 3. Sunscreen
    sunscreen_keywords = ['sunscreen', 'spf', 'sun protection', 'uv protection', 'sunblock']
    if any(keyword in message_lower for keyword in sunscreen_keywords):
        skin_type_advice = ""
        if previous_context == 'oily':
            skin_type_advice = "For oily skin, use gel-based or matte finish sunscreens that are non-comedogenic."
        elif previous_context == 'dry':
            skin_type_advice = "For dry skin, look for hydrating sunscreens with moisturizing ingredients."
        elif previous_context == 'sensitive':
            skin_type_advice = "For sensitive skin, use mineral sunscreens (zinc oxide, titanium dioxide) which are less likely to cause irritation."
        
        return f"Sunscreen is the #1 anti-aging product! Here's what you need to know:\n\n**SPF Requirements:**\n- Use SPF 30 or higher daily\n- Broad-spectrum protection (UVA + UVB)\n- Apply 15-30 minutes before sun exposure\n- Reapply every 2 hours when outdoors\n- Use even on cloudy days (UV rays penetrate clouds)\n\n**Application:**\n- Use about 1/4 teaspoon for face and neck\n- Don't forget ears, neck, and décolletage\n- Apply as last step in morning routine\n\n{skin_type_advice}\n\n**Pro Tip:** Sunscreen prevents 90% of skin aging, dark spots, and skin cancer. It's non-negotiable!"
    
    # 4. Moisturizer
    moisturizer_keywords = ['moisturize', 'moisturizer', 'moisture', 'hydrate', 'hydration', 'cream', 'lotion']
    if any(keyword in message_lower for keyword in moisturizer_keywords):
        skin_type_recs = {
            'oily': "Use lightweight, oil-free, gel-based moisturizers. Look for 'non-comedogenic' label.",
            'dry': "Use rich creams with ceramides, hyaluronic acid, and oils. Apply to damp skin for better absorption.",
            'combination': "Use lightweight lotions, or apply different products to different areas (lighter on T-zone).",
            'sensitive': "Use fragrance-free, hypoallergenic moisturizers with minimal ingredients.",
            'normal': "Any good quality moisturizer works. Look for ones with antioxidants and SPF for day use."
        }
        rec = skin_type_recs.get(previous_context, "Choose based on your skin's needs - lightweight for day, richer for night.")
        
        return f"Moisturizing is essential for ALL skin types! Here's why and how:\n\n**Why Everyone Needs Moisturizer:**\n- Even oily skin needs hydration (moisturizer ≠ oil)\n- Helps maintain skin barrier function\n- Prevents overproduction of oil (dry skin can trigger more oil)\n- Keeps skin plump and youthful\n\n**When to Apply:**\n- Morning: After serums, before sunscreen\n- Night: After treatments, as final step\n- Apply to slightly damp skin for better absorption\n\n**Ingredients to Look For:**\n- Hyaluronic acid (hydration)\n- Ceramides (barrier repair)\n- Niacinamide (oil control, brightening)\n- Glycerin (hydration)\n\n**For Your Skin Type:**\n{rec}"
    
    # 5. Routine questions
    routine_keywords = ['routine', 'regimen', 'skincare routine', 'daily routine', 'morning routine', 'night routine']
    if any(keyword in message_lower for keyword in routine_keywords):
        morning = "**Morning Routine:**\n1. Cleanser (gentle)\n2. Serum (vitamin C, niacinamide, or hyaluronic acid)\n3. Moisturizer\n4. Sunscreen (SPF 30+)\n\n"
        night = "**Night Routine:**\n1. Makeup remover (if wearing makeup)\n2. Cleanser (double cleanse if needed)\n3. Treatment serum (retinol, AHA/BHA, or targeted treatment)\n4. Eye cream (optional)\n5. Moisturizer or night cream\n\n"
        return f"Here's a complete skincare routine:\n\n{morning}{night}**General Tips:**\n- Start simple: cleanser, moisturizer, sunscreen\n- Add products gradually (one at a time, wait 2 weeks)\n- Patch test new products\n- Be consistent (skincare takes 4-6 weeks to show results)\n- Adjust based on your skin's response\n\n**For {previous_context or 'your'} skin:** Adjust product textures and active ingredients based on your specific needs!"
    
    # 6. Oily skin
    oily_keywords = ['oily', 'oiliness', 'greasy', 'shiny', 'sebum', 'excess oil']
    if any(keyword in message_lower for keyword in oily_keywords):
        return f"Managing oily skin effectively:\n\n**Cleansing:**\n- Use gel or foaming cleanser (not harsh soap)\n- Cleanse twice daily (over-cleansing strips skin and increases oil)\n- Look for salicylic acid or niacinamide in cleanser\n\n**Moisturizing:**\n- YES, you still need moisturizer! Use oil-free, gel-based formulas\n- Lightweight, non-comedogenic products\n- Hyaluronic acid serums provide hydration without oil\n\n**Products:**\n- Oil-free everything (moisturizer, sunscreen, makeup)\n- Non-comedogenic labels\n- Mattifying products for daytime\n- Salicylic acid for pore control\n- Niacinamide (2-5%) for oil regulation\n\n**Lifestyle:**\n- Don't over-cleanse\n- Use blotting papers instead of washing more\n- Avoid heavy, pore-clogging products\n- Manage stress (triggers oil production)\n\n**Myth Buster:** Skipping moisturizer makes oily skin worse by triggering more oil production!"
    
    # 7. Dark circles
    dark_circle_keywords = ['dark circles', 'under eye', 'eye bags', 'puffy eyes', 'eye circles', 'bags under eyes']
    if any(keyword in message_lower for keyword in dark_circle_keywords):
        return f"Addressing dark circles and under-eye concerns:\n\n**Causes:**\n- Genetics (thinner skin under eyes)\n- Lack of sleep (7-9 hours recommended)\n- Allergies\n- Dehydration\n- Aging\n- Sun damage\n\n**Solutions:**\n1. **Sleep**: Get 7-9 hours of quality sleep\n2. **Hydration**: Drink plenty of water\n3. **Eye Creams**:\n   - Caffeine (temporary tightening)\n   - Retinol (long-term improvement)\n   - Vitamin C (brightening)\n   - Peptides (firming)\n4. **Cold Compresses**: Reduce puffiness\n5. **Sunscreen**: Prevent further darkening\n6. **Concealer**: Color corrector (peach/orange tones)\n\n**When to See a Doctor:**\nIf dark circles are severe, sudden, or accompanied by other symptoms, consult a dermatologist. Some cases may need medical treatment."
    
    # 8. Wrinkles/Aging
    aging_keywords = ['wrinkle', 'aging', 'anti-aging', 'fine lines', 'age', 'old', 'mature skin', 'sagging']
    if any(keyword in message_lower for keyword in aging_keywords):
        return f"Anti-aging skincare strategy:\n\n**Prevention (Most Important!):**\n- Sunscreen daily (prevents 90% of aging)\n- Don't smoke\n- Limit alcohol\n- Get enough sleep\n- Stay hydrated\n- Healthy diet (antioxidants)\n\n**Active Ingredients:**\n1. **Retinol/Retinoids**: Gold standard for wrinkles\n   - Start with 0.25-0.5%, increase gradually\n   - Use at night only\n   - Build tolerance slowly\n2. **Vitamin C**: Brightens, protects from damage\n   - Use in morning\n   - L-ascorbic acid form is most effective\n3. **Peptides**: Help with firmness\n4. **Hyaluronic Acid**: Plumps skin, reduces fine lines appearance\n5. **Niacinamide**: Improves texture and tone\n\n**Routine:**\n- Morning: Vitamin C serum → Moisturizer → SPF 30+\n- Night: Retinol → Moisturizer\n- Start retinol 2-3x per week, increase to nightly\n\n**Professional Treatments:**\nFor significant results, consider dermatologist treatments like prescription retinoids, chemical peels, or laser therapy."
    
    # 9. Sensitive skin
    sensitive_keywords = ['sensitive', 'irritation', 'redness', 'stinging', 'burning', 'reactive', 'allergic']
    if any(keyword in message_lower for keyword in sensitive_keywords):
        return f"Caring for sensitive skin:\n\n**Product Selection:**\n- Fragrance-free (including essential oils)\n- Dye-free\n- Minimal ingredient lists\n- Hypoallergenic formulas\n- pH-balanced (around 5.5)\n- Avoid alcohol, harsh acids, and strong actives\n\n**Routine:**\n- Gentle, creamy cleansers (not foaming)\n- Minimal products (less is more)\n- Introduce ONE new product at a time\n- Always patch test (48 hours on inner arm)\n- Use lukewarm water (never hot)\n- Pat dry (don't rub)\n\n**Ingredients to Avoid:**\n- Fragrance and essential oils\n- Alcohol (denatured alcohol)\n- Harsh acids (start with very low concentrations)\n- Physical scrubs\n- Hot water\n\n**Ingredients That Help:**\n- Ceramides (barrier repair)\n- Niacinamide (calming, in low concentrations)\n- Centella asiatica (calming)\n- Oat extract (soothing)\n- Hyaluronic acid (gentle hydration)\n\n**When to See a Doctor:**\nIf you experience persistent redness, burning, or reactions, see a dermatologist to rule out conditions like rosacea or contact dermatitis."
    
    # 10. Cleansers
    cleanser_keywords = ['cleanser', 'cleansing', 'wash', 'soap', 'face wash', 'cleaning']
    if any(keyword in message_lower for keyword in cleanser_keywords):
        skin_type_cleanser = {
            'oily': "Gel or foaming cleansers with salicylic acid or niacinamide",
            'dry': "Cream or milk cleansers, hydrating formulas",
            'sensitive': "Gentle, fragrance-free, cream-based cleansers",
            'combination': "Balancing cleansers, or use different cleansers for different areas"
        }
        rec = skin_type_cleanser.get(previous_context, "Choose based on your skin type and concerns")
        
        return f"Choosing the right cleanser:\n\n**For {previous_context or 'your'} skin:** {rec}\n\n**Key Principles:**\n- Cleanse twice daily (morning and night)\n- Use lukewarm water (not hot or cold)\n- Cleanse for 60 seconds (allows active ingredients to work)\n- Be gentle (no scrubbing)\n- pH-balanced formulas (around 5.5)\n- Should leave skin clean but not tight or stripped\n\n**Double Cleansing:**\nIf you wear makeup or sunscreen:\n1. Oil-based cleanser (removes makeup, sunscreen)\n2. Water-based cleanser (deep clean)\n\n**Ingredients to Look For:**\n- Salicylic acid (oily, acne-prone)\n- Ceramides (dry, sensitive)\n- Hyaluronic acid (hydration)\n- Niacinamide (oil control)\n\n**Avoid:**\n- Harsh soaps (high pH)\n- Over-cleansing (strips natural oils)\n- Hot water (dries out skin)"
    
    # 11. Serums
    serum_keywords = ['serum', 'serums', 'treatment', 'active', 'vitamin c', 'retinol', 'niacinamide']
    if any(keyword in message_lower for keyword in serum_keywords):
        return f"Understanding serums:\n\n**What are Serums?**\nConcentrated treatments with active ingredients in smaller molecules for deeper penetration.\n\n**Popular Serums:**\n1. **Vitamin C** (Morning)\n   - Brightens, protects from UV damage\n   - Use L-ascorbic acid form (15-20%)\n   - Apply before moisturizer\n\n2. **Retinol** (Night)\n   - Anti-aging, acne treatment\n   - Start with 0.25-0.5%\n   - Build tolerance gradually\n   - Use 2-3x per week initially\n\n3. **Niacinamide** (Any time)\n   - Oil control, pore refinement\n   - Brightening, anti-inflammatory\n   - 2-5% concentration\n   - Can be used daily\n\n4. **Hyaluronic Acid** (Any time)\n   - Intense hydration\n   - Plumps skin\n   - Use before heavier products\n\n5. **AHA/BHA** (Night, 2-3x per week)\n   - Chemical exfoliation\n   - AHA: surface exfoliation\n   - BHA: penetrates pores\n\n**How to Use:**\n- Apply after cleansing, before moisturizer\n- Use 2-3 drops\n- Pat gently into skin\n- Wait 1-2 minutes before next product\n- Start with one serum, add others gradually\n- Layer from thinnest to thickest consistency"
    
    # 12. Product recommendations
    product_keywords = ['product', 'recommend', 'best', 'buy', 'ingredient', 'brand']
    if any(keyword in message_lower for keyword in product_keywords):
        return f"I can help with product recommendations! Here's what to look for:\n\n**Key Ingredients by Concern:**\n- **Acne**: Salicylic acid, benzoyl peroxide, niacinamide\n- **Anti-aging**: Retinol, vitamin C, peptides, hyaluronic acid\n- **Brightening**: Vitamin C, niacinamide, alpha arbutin\n- **Hydration**: Hyaluronic acid, glycerin, ceramides\n- **Oil Control**: Niacinamide, salicylic acid, clay\n\n**Product Labels to Look For:**\n- Non-comedogenic (won't clog pores)\n- Fragrance-free (for sensitive skin)\n- Oil-free (for oily skin)\n- Broad-spectrum SPF (sunscreens)\n\n**Tips:**\n- Read ingredient lists\n- Start with drugstore options (many are excellent)\n- Patch test new products\n- Introduce one product at a time\n- Give products 4-6 weeks to work\n\n**For personalized recommendations**, try our skin analysis feature to get customized product suggestions based on your skin type!"
    
    # 13. Diet/Nutrition
    diet_keywords = ['diet', 'food', 'nutrition', 'eat', 'drink', 'vitamin', 'supplement']
    if any(keyword in message_lower for keyword in diet_keywords):
        return f"Diet and nutrition for healthy skin:\n\n**Foods That Help Skin:**\n- **Antioxidants**: Berries, dark leafy greens, tomatoes\n- **Omega-3**: Fish, walnuts, flaxseeds (reduce inflammation)\n- **Vitamin C**: Citrus, bell peppers, strawberries (collagen production)\n- **Vitamin E**: Nuts, seeds, avocado (protection)\n- **Zinc**: Nuts, seeds, whole grains (healing, acne)\n- **Water**: Stay hydrated (8+ glasses daily)\n\n**Foods to Limit:**\n- High glycemic foods (sugar, white bread) - can worsen acne\n- Dairy (some people find it triggers acne)\n- Processed foods\n- Excessive alcohol\n\n**Supplements:**\n- Omega-3 (anti-inflammatory)\n- Vitamin D (immune function)\n- Probiotics (gut health = skin health)\n- Collagen peptides (may help with aging)\n\n**Remember:**\n- Healthy diet supports healthy skin\n- Stay hydrated\n- Limit sugar and processed foods\n- Consult a doctor before taking supplements\n- Diet complements skincare, doesn't replace it"
    
    # 14. General skin health
    health_keywords = ['healthy skin', 'skin health', 'improve skin', 'better skin', 'glowing skin']
    if any(keyword in message_lower for keyword in health_keywords):
        return f"Achieving healthy, glowing skin:\n\n**Daily Essentials:**\n1. **Cleanse** gently twice daily\n2. **Moisturize** to maintain barrier\n3. **Protect** with SPF 30+ daily\n4. **Hydrate** from within (drink water)\n\n**Weekly:**\n- Exfoliate 1-2 times\n- Use treatment masks\n- Get adequate sleep (7-9 hours)\n\n**Lifestyle:**\n- Balanced diet (antioxidants, omega-3)\n- Regular exercise (increases circulation)\n- Manage stress\n- Don't smoke\n- Limit alcohol\n- Get enough sleep\n\n**Professional Care:**\n- Regular dermatologist visits\n- Annual skin cancer checks\n- Professional treatments if needed\n\n**Patience:**\n- Skincare takes 4-6 weeks to show results\n- Be consistent with routine\n- Don't overdo it (less can be more)\n- Listen to your skin\n\nRemember: Healthy skin is a journey, not a destination!"
    
    # 15. Combination skin
    if 'combination' in message_lower or 'combo' in message_lower:
        return f"Caring for combination skin:\n\n**The Challenge:**\nCombination skin has both oily (T-zone: forehead, nose, chin) and dry/normal (cheeks) areas.\n\n**Strategy:**\n- Use different products for different areas\n- Or use balancing products that work for both\n\n**Cleanser:**\n- Gel or balancing cleanser\n- Focus on T-zone, be gentle on cheeks\n\n**Moisturizer:**\n- Lightweight lotion overall\n- Add extra moisture to dry areas if needed\n- Oil-free on T-zone\n\n**Treatments:**\n- Salicylic acid on T-zone (oil control)\n- Hydrating serums on cheeks\n- Exfoliate 2-3x per week\n\n**Sunscreen:**\n- Lightweight, non-comedogenic\n- Gel or matte finish preferred\n\n**Tips:**\n- Don't over-treat oily areas (can cause more oil)\n- Don't skip moisturizer on dry areas\n- Adjust routine based on season (skin changes)"
    
    # Default/fallback response with helpful suggestions
    if len(message_lower.split()) < 3:  # Very short messages
        return "I'd love to help! Could you tell me more about what you're looking for? For example:\n- Your skin type or concerns\n- Specific products or ingredients\n- Routine questions\n- Or ask about: acne, wrinkles, dark circles, sensitive skin, etc.\n\nWhat would you like to know? 😊"
    
    # Contextual responses based on previous conversation
    if history and len(history) > 0:
        last_topic = history[-1]['bot'].lower()
        if 'acne' in last_topic or 'pimple' in last_topic:
            return "Is there something specific about acne treatment you'd like to know more about? I can help with routines, products, or when to see a dermatologist."
        if 'routine' in last_topic:
            return "Would you like me to help you customize your routine based on your skin type or specific concerns?"
    
    # Generic helpful response
    return "I'm here to help with your skincare questions! I can assist with:\n\n• **Skin concerns**: Acne, wrinkles, dark circles, sensitivity\n• **Routines**: Morning, night, and weekly routines\n• **Products**: Cleansers, moisturizers, serums, sunscreens\n• **Skin types**: Oily, dry, combination, sensitive, normal\n• **Ingredients**: What to look for and avoid\n• **General advice**: Diet, lifestyle, and skin health\n\nWhat specific topic would you like to know more about? You can also try our skin analysis feature for personalized recommendations! 😊"
