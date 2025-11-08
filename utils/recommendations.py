def get_skincare_recommendations(skin_type, analysis):
    """
    Generate personalized skincare recommendations based on skin type and analysis
    Returns: Dictionary with products, routines, and tips
    """
    recommendations = {
        'skin_type': skin_type,
        'products': [],
        'morning_routine': [],
        'night_routine': [],
        'diet_tips': [],
        'hydration_tips': [],
        'general_tips': []
    }
    
    # Base recommendations by skin type
    if skin_type == 'Dry':
        recommendations['products'] = [
            'Gentle hydrating cleanser',
            'Hyaluronic acid serum',
            'Rich moisturizer with ceramides',
            'SPF 30+ sunscreen',
            'Night cream with peptides'
        ]
        recommendations['morning_routine'] = [
            'Cleanse with gentle hydrating cleanser',
            'Apply hyaluronic acid serum',
            'Moisturize with rich cream',
            'Apply sunscreen (SPF 30+)'
        ]
        recommendations['night_routine'] = [
            'Remove makeup with oil-based cleanser',
            'Cleanse with gentle cleanser',
            'Apply hydrating serum',
            'Moisturize with night cream',
            'Use facial oil if needed'
        ]
        recommendations['diet_tips'] = [
            'Increase omega-3 fatty acids (fish, walnuts)',
            'Eat foods rich in vitamin E (nuts, seeds)',
            'Stay hydrated with 8+ glasses of water daily',
            'Include avocados and olive oil in your diet'
        ]
        recommendations['hydration_tips'] = [
            'Drink 8-10 glasses of water daily',
            'Use a humidifier in dry environments',
            'Avoid hot showers (use lukewarm water)',
            'Apply moisturizer immediately after washing'
        ]
    
    elif skin_type == 'Oily':
        recommendations['products'] = [
            'Foaming cleanser with salicylic acid',
            'Oil-free moisturizer',
            'Niacinamide serum',
            'SPF 30+ non-comedogenic sunscreen',
            'Clay mask (2-3 times per week)'
        ]
        recommendations['morning_routine'] = [
            'Cleanse with foaming cleanser',
            'Apply niacinamide serum',
            'Moisturize with oil-free lotion',
            'Apply non-comedogenic sunscreen'
        ]
        recommendations['night_routine'] = [
            'Double cleanse (oil + water-based)',
            'Use BHA/AHA exfoliant (2-3 times/week)',
            'Apply lightweight moisturizer',
            'Spot treatment for acne if needed'
        ]
        recommendations['diet_tips'] = [
            'Reduce dairy and high-glycemic foods',
            'Increase green leafy vegetables',
            'Include zinc-rich foods (nuts, seeds)',
            'Limit processed and fried foods'
        ]
        recommendations['hydration_tips'] = [
            'Use oil-free, non-comedogenic products',
            'Don\'t skip moisturizer (use lightweight)',
            'Stay hydrated with water throughout the day',
            'Avoid over-washing (max 2x daily)'
        ]
    
    elif skin_type == 'Combination':
        recommendations['products'] = [
            'Balancing cleanser',
            'Lightweight moisturizer',
            'Vitamin C serum',
            'SPF 30+ sunscreen',
            'Exfoliating toner (for T-zone)'
        ]
        recommendations['morning_routine'] = [
            'Cleanse with balancing cleanser',
            'Apply vitamin C serum',
            'Moisturize (lighter on T-zone)',
            'Apply sunscreen'
        ]
        recommendations['night_routine'] = [
            'Double cleanse',
            'Use exfoliating toner on T-zone',
            'Apply serum',
            'Moisturize (adjust based on zone)'
        ]
        recommendations['diet_tips'] = [
            'Maintain balanced diet',
            'Stay hydrated',
            'Include antioxidants (berries, green tea)',
            'Moderate dairy intake'
        ]
        recommendations['hydration_tips'] = [
            'Use different products for different zones',
            'Moisturize dry areas more',
            'Keep T-zone matte',
            'Drink adequate water daily'
        ]
    
    else:  # Normal
        recommendations['products'] = [
            'Gentle cleanser',
            'Balanced moisturizer',
            'Antioxidant serum',
            'SPF 30+ sunscreen',
            'Weekly exfoliant'
        ]
        recommendations['morning_routine'] = [
            'Cleanse with gentle cleanser',
            'Apply antioxidant serum',
            'Moisturize',
            'Apply sunscreen'
        ]
        recommendations['night_routine'] = [
            'Remove makeup',
            'Cleanse',
            'Apply serum',
            'Moisturize',
            'Weekly exfoliation'
        ]
        recommendations['diet_tips'] = [
            'Maintain healthy balanced diet',
            'Include variety of fruits and vegetables',
            'Stay hydrated',
            'Limit processed foods'
        ]
        recommendations['hydration_tips'] = [
            'Maintain consistent routine',
            'Drink 8 glasses of water daily',
            'Protect from sun exposure',
            'Get adequate sleep'
        ]
    
    # Add specific recommendations based on analysis
    if analysis.get('acne_spots', {}).get('severity', 0) > 15:
        recommendations['general_tips'].append('Consider salicylic acid or benzoyl peroxide for acne')
        recommendations['general_tips'].append('Avoid touching your face frequently')
        recommendations['general_tips'].append('Change pillowcases regularly')
    
    if analysis.get('dark_circles', {}).get('severity', 0) > 20:
        recommendations['general_tips'].append('Get 7-9 hours of sleep nightly')
        recommendations['general_tips'].append('Use eye cream with caffeine or retinol')
        recommendations['general_tips'].append('Apply cold compresses to reduce puffiness')
    
    if analysis.get('redness', {}).get('severity', 0) > 15:
        recommendations['general_tips'].append('Use gentle, fragrance-free products')
        recommendations['general_tips'].append('Avoid hot water and harsh exfoliants')
        recommendations['general_tips'].append('Consider products with niacinamide or centella asiatica')
    
    if analysis.get('uneven_tone', {}).get('score', 0) > 20:
        recommendations['general_tips'].append('Use vitamin C serum in the morning')
        recommendations['general_tips'].append('Apply retinol at night (start slow)')
        recommendations['general_tips'].append('Always use sunscreen to prevent further darkening')
    
    if not recommendations['general_tips']:
        recommendations['general_tips'] = [
            'Maintain consistent skincare routine',
            'Always wear sunscreen',
            'Stay hydrated',
            'Get adequate sleep',
            'Eat a balanced diet'
        ]
    
    return recommendations

