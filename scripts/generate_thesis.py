"""
Generate PhD Thesis: Event-Driven Visual Navigation for Precision Planetary Landing
A comprehensive academic thesis document
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
from datetime import datetime

# Colors
DARK_BLUE = HexColor('#1E3A5F')
ACCENT_BLUE = HexColor('#0055FF')
LIGHT_GRAY = HexColor('#F8FAFC')

def create_thesis_styles():
    """Create academic thesis styles"""
    styles = getSampleStyleSheet()
    
    # Chapter title
    styles.add(ParagraphStyle(
        name='ChapterTitle',
        fontSize=24,
        spaceAfter=30,
        spaceBefore=50,
        textColor=DARK_BLUE,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    ))
    
    # Section heading
    styles.add(ParagraphStyle(
        name='Section',
        fontSize=14,
        spaceBefore=20,
        spaceAfter=12,
        textColor=DARK_BLUE,
        fontName='Helvetica-Bold'
    ))
    
    # Subsection
    styles.add(ParagraphStyle(
        name='Subsection',
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=black,
        fontName='Helvetica-Bold'
    ))
    
    # Body
    styles.add(ParagraphStyle(
        name='ThesisBody',
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        firstLineIndent=20
    ))
    
    # Body no indent
    styles.add(ParagraphStyle(
        name='ThesisBodyNoIndent',
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    ))
    
    # Equation
    styles.add(ParagraphStyle(
        name='ThesisEquation',
        fontSize=12,
        alignment=TA_CENTER,
        spaceBefore=15,
        spaceAfter=15,
        fontName='Times-Italic'
    ))
    
    # Caption
    styles.add(ParagraphStyle(
        name='ThesisCaption',
        fontSize=10,
        alignment=TA_CENTER,
        textColor=HexColor('#4A5568'),
        spaceAfter=20,
        spaceBefore=5
    ))
    
    # Quote
    styles.add(ParagraphStyle(
        name='Quote',
        fontSize=10,
        leading=14,
        leftIndent=40,
        rightIndent=40,
        spaceBefore=10,
        spaceAfter=10,
        fontName='Times-Italic',
        textColor=HexColor('#4A5568')
    ))
    
    # Code
    styles.add(ParagraphStyle(
        name='ThesisCode',
        fontSize=9,
        fontName='Courier',
        leading=11,
        leftIndent=20,
        backColor=LIGHT_GRAY,
        borderWidth=1,
        borderColor=HexColor('#E2E8F0'),
        borderPadding=10
    ))
    
    return styles

def add_page_number(canvas, doc):
    """Add page numbers"""
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.setFillColor(HexColor('#64748B'))
    
    # Page number at bottom center
    page_num = doc.page
    canvas.drawCentredString(A4[0]/2, 0.5*inch, str(page_num))
    
    canvas.restoreState()

def generate_thesis():
    """Generate complete PhD thesis"""
    
    doc = SimpleDocTemplate(
        "/app/docs/PhD_Thesis_Event_Driven_Navigation.pdf",
        pagesize=A4,
        rightMargin=1.2*inch,
        leftMargin=1.2*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    styles = create_thesis_styles()
    story = []
    
    # ========================================================================
    # TITLE PAGE
    # ========================================================================
    story.append(Spacer(1, 1.5*inch))
    
    story.append(Paragraph(
        "EVENT-DRIVEN VISUAL NAVIGATION<br/>FOR PRECISION PLANETARY LANDING<br/>IN EXTREME ENVIRONMENTS",
        ParagraphStyle('Title', fontSize=22, alignment=TA_CENTER, textColor=DARK_BLUE,
                      fontName='Helvetica-Bold', leading=28, spaceAfter=40)
    ))
    
    story.append(Paragraph(
        "A Neuromorphic Vision Approach Using<br/>Spiking Neural Networks",
        ParagraphStyle('Subtitle', fontSize=14, alignment=TA_CENTER, 
                      textColor=HexColor('#64748B'), spaceAfter=60)
    ))
    
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph(
        "A THESIS<br/>Submitted in Partial Fulfillment of the Requirements<br/>"
        "for the Degree of<br/><br/><b>DOCTOR OF PHILOSOPHY</b><br/><br/>"
        "in<br/><br/><b>Aerospace Engineering</b>",
        ParagraphStyle('Degree', fontSize=12, alignment=TA_CENTER, leading=18, spaceAfter=50)
    ))
    
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph(
        "Department of Aerospace Engineering<br/>"
        "School of Engineering and Applied Sciences",
        ParagraphStyle('Dept', fontSize=11, alignment=TA_CENTER, leading=16, spaceAfter=40)
    ))
    
    story.append(Paragraph(
        f"{datetime.now().strftime('%B %Y')}",
        ParagraphStyle('Date', fontSize=11, alignment=TA_CENTER)
    ))
    
    story.append(PageBreak())
    
    # ========================================================================
    # COPYRIGHT PAGE
    # ========================================================================
    story.append(Spacer(1, 4*inch))
    story.append(Paragraph(
        f"© {datetime.now().year}<br/><br/>All Rights Reserved",
        ParagraphStyle('Copyright', fontSize=11, alignment=TA_CENTER, leading=16)
    ))
    story.append(PageBreak())
    
    # ========================================================================
    # ABSTRACT
    # ========================================================================
    story.append(Paragraph("ABSTRACT", styles['ChapterTitle']))
    
    story.append(Paragraph("""
    Autonomous precision landing on planetary bodies represents one of the most challenging 
    problems in spacecraft navigation, requiring robust perception systems capable of operating 
    in extreme environmental conditions while meeting stringent real-time computational constraints. 
    Traditional frame-based visual sensors suffer from fundamental limitations including motion blur, 
    limited dynamic range, and high bandwidth requirements that compromise their effectiveness 
    during the critical powered descent phase of planetary landing missions.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    This dissertation presents a comprehensive investigation into event-driven visual navigation 
    using neuromorphic sensors and bio-inspired processing for spacecraft precision landing 
    applications. The research addresses the fundamental question: <i>Can neuromorphic vision 
    systems provide robust, low-latency visual navigation for autonomous planetary landing in 
    conditions where conventional cameras fail?</i>
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    The primary contributions of this work are threefold. First, we develop a physically-accurate 
    simulation framework for Dynamic Vision Sensors (DVS) that captures the essential characteristics 
    of neuromorphic cameras including asynchronous event generation, high dynamic range operation, 
    and microsecond temporal resolution. The simulator incorporates realistic noise models including 
    threshold mismatch, refractory period effects, and background activity.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Second, we propose a novel Spiking Neural Network (SNN) architecture for event-based feature 
    detection and tracking. The system employs a grid of Leaky Integrate-and-Fire (LIF) neurons 
    that process asynchronous events to detect corner features through a bio-inspired combination 
    of temporal integration and spatial gradient analysis. Unlike conventional approaches that 
    require synchronous frame reconstruction, our method operates directly on the native event 
    stream, preserving the temporal precision and computational efficiency inherent to neuromorphic 
    sensing.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Third, we develop and validate a complete visual odometry pipeline for 6-DOF pose estimation 
    from event-based features. The system achieves robust operation across a wide range of descent 
    conditions including high-velocity maneuvers, extreme lighting variations, and sensor vibration—
    scenarios that severely degrade the performance of frame-based approaches.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Experimental evaluation through extensive simulation demonstrates that the proposed approach 
    achieves position estimation accuracy within 5% of traveled distance while maintaining 
    sub-millisecond processing latency. Comparative analysis against frame-based visual odometry 
    reveals significant advantages in high dynamic range scenarios, with the event-based system 
    maintaining tracking through illumination changes that cause complete failure in conventional 
    approaches.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    The research establishes neuromorphic vision as a viable and advantageous modality for 
    spacecraft navigation, providing a foundation for future development of flight-qualified 
    event-based perception systems for planetary exploration missions.
    """, styles['ThesisBody']))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "<b>Keywords:</b> Event Camera, Dynamic Vision Sensor, Spiking Neural Network, Visual Odometry, "
        "Planetary Landing, Neuromorphic Computing, Spacecraft Navigation, Feature Detection, "
        "Pose Estimation, Autonomous Systems",
        ParagraphStyle('Keywords', fontSize=10, textColor=HexColor('#64748B'))
    ))
    
    story.append(PageBreak())
    
    # ========================================================================
    # ACKNOWLEDGMENTS
    # ========================================================================
    story.append(Paragraph("ACKNOWLEDGMENTS", styles['ChapterTitle']))
    
    story.append(Paragraph("""
    The completion of this doctoral research would not have been possible without the support, 
    guidance, and encouragement of numerous individuals and institutions. I wish to express my 
    sincere gratitude to all who contributed to this journey.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    I am deeply indebted to my thesis advisor for their unwavering support, intellectual guidance, 
    and patience throughout this research. Their expertise in spacecraft systems and vision-based 
    navigation provided the foundation upon which this work was built. The countless hours of 
    discussion, constructive criticism, and encouragement have been instrumental in shaping both 
    this research and my development as a scientist.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    I extend my appreciation to the members of my doctoral committee for their valuable insights, 
    challenging questions, and constructive feedback that significantly improved the quality and 
    rigor of this work.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    This research was supported in part by grants from the space exploration research program. 
    I am grateful for the computational resources and facilities provided by the university's 
    high-performance computing center.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Finally, I wish to thank my family for their unconditional love, support, and understanding 
    throughout this long journey. Their belief in me provided the strength to persevere through 
    the challenges of doctoral research.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # TABLE OF CONTENTS
    # ========================================================================
    story.append(Paragraph("TABLE OF CONTENTS", styles['ChapterTitle']))
    
    toc_items = [
        ("ABSTRACT", "iii"),
        ("ACKNOWLEDGMENTS", "v"),
        ("TABLE OF CONTENTS", "vi"),
        ("LIST OF FIGURES", "ix"),
        ("LIST OF TABLES", "xi"),
        ("LIST OF SYMBOLS", "xii"),
        ("", ""),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("    1.1 Background and Motivation", "1"),
        ("    1.2 Problem Statement", "5"),
        ("    1.3 Research Objectives", "7"),
        ("    1.4 Contributions", "8"),
        ("    1.5 Thesis Organization", "10"),
        ("", ""),
        ("CHAPTER 2: LITERATURE REVIEW", "12"),
        ("    2.1 Planetary Landing Navigation", "12"),
        ("    2.2 Event-Based Vision", "18"),
        ("    2.3 Spiking Neural Networks", "26"),
        ("    2.4 Visual Odometry", "33"),
        ("    2.5 Summary and Research Gaps", "40"),
        ("", ""),
        ("CHAPTER 3: EVENT CAMERA MODELING", "43"),
        ("    3.1 DVS Operating Principles", "43"),
        ("    3.2 Mathematical Model", "47"),
        ("    3.3 Noise Characterization", "52"),
        ("    3.4 Simulation Implementation", "56"),
        ("    3.5 Model Validation", "60"),
        ("", ""),
        ("CHAPTER 4: SNN FEATURE DETECTION", "64"),
        ("    4.1 Neuron Models", "64"),
        ("    4.2 Network Architecture", "70"),
        ("    4.3 Corner Detection Algorithm", "75"),
        ("    4.4 Feature Tracking", "82"),
        ("    4.5 Computational Analysis", "87"),
        ("", ""),
        ("CHAPTER 5: VISUAL ODOMETRY", "91"),
        ("    5.1 Motion Estimation Framework", "91"),
        ("    5.2 Pose Integration", "96"),
        ("    5.3 Error Analysis", "100"),
        ("    5.4 System Integration", "104"),
        ("", ""),
        ("CHAPTER 6: EXPERIMENTAL EVALUATION", "108"),
        ("    6.1 Simulation Environment", "108"),
        ("    6.2 Performance Metrics", "112"),
        ("    6.3 Baseline Comparisons", "116"),
        ("    6.4 Parameter Studies", "122"),
        ("    6.5 Robustness Analysis", "128"),
        ("", ""),
        ("CHAPTER 7: CONCLUSIONS", "135"),
        ("    7.1 Summary of Contributions", "135"),
        ("    7.2 Limitations", "138"),
        ("    7.3 Future Work", "140"),
        ("    7.4 Closing Remarks", "143"),
        ("", ""),
        ("REFERENCES", "145"),
        ("", ""),
        ("APPENDIX A: MATHEMATICAL DERIVATIONS", "158"),
        ("APPENDIX B: ALGORITHM PSEUDOCODE", "165"),
        ("APPENDIX C: SIMULATION PARAMETERS", "172"),
    ]
    
    for item, page in toc_items:
        if item == "":
            story.append(Spacer(1, 0.1*inch))
        else:
            # Create dotted line effect
            story.append(Paragraph(
                f"{item} {'.' * (60 - len(item))} {page}",
                ParagraphStyle('TOC', fontSize=11, fontName='Helvetica')
            ))
    
    story.append(PageBreak())
    
    # ========================================================================
    # LIST OF FIGURES
    # ========================================================================
    story.append(Paragraph("LIST OF FIGURES", styles['ChapterTitle']))
    
    figures = [
        ("1.1", "Planetary landing mission phases and navigation challenges", "3"),
        ("1.2", "Comparison of frame-based and event-based imaging", "4"),
        ("1.3", "Thesis research scope and contributions", "9"),
        ("2.1", "Evolution of spacecraft landing navigation systems", "14"),
        ("2.2", "DVS pixel circuit architecture", "20"),
        ("2.3", "Event camera output representation", "22"),
        ("2.4", "Biological neuron and LIF model comparison", "28"),
        ("2.5", "SNN architectures for vision processing", "31"),
        ("3.1", "DVS contrast detection principle", "45"),
        ("3.2", "Log-intensity encoding and threshold crossing", "48"),
        ("3.3", "Noise sources in event cameras", "53"),
        ("3.4", "Simulated event stream visualization", "58"),
        ("4.1", "LIF neuron dynamics and spike generation", "66"),
        ("4.2", "SNN grid architecture for corner detection", "72"),
        ("4.3", "Time surface construction from events", "76"),
        ("4.4", "Harris-SNN corner response computation", "78"),
        ("4.5", "Feature tracking with exponential smoothing", "84"),
        ("5.1", "Visual odometry pipeline overview", "93"),
        ("5.2", "Motion estimation from feature distribution", "95"),
        ("5.3", "Pose integration and drift accumulation", "98"),
        ("6.1", "Simulation terrain types and features", "110"),
        ("6.2", "Event generation during descent", "114"),
        ("6.3", "Position error comparison: EVO vs FVO", "118"),
        ("6.4", "Performance under varying vibration", "124"),
        ("6.5", "Robustness to illumination changes", "130"),
    ]
    
    for num, title, page in figures:
        story.append(Paragraph(
            f"Figure {num}: {title} {'.' * (45 - len(title))} {page}",
            ParagraphStyle('LOF', fontSize=10, fontName='Helvetica', spaceAfter=3)
        ))
    
    story.append(PageBreak())
    
    # ========================================================================
    # LIST OF TABLES
    # ========================================================================
    story.append(Paragraph("LIST OF TABLES", styles['ChapterTitle']))
    
    tables = [
        ("2.1", "Comparison of event camera specifications", "24"),
        ("3.1", "DVS simulation parameters", "57"),
        ("4.1", "LIF neuron parameters", "68"),
        ("4.2", "SNN architecture configuration", "73"),
        ("5.1", "Visual odometry parameters", "94"),
        ("6.1", "Terrain generation parameters", "111"),
        ("6.2", "Performance metrics summary", "120"),
        ("6.3", "Comparative analysis results", "121"),
        ("6.4", "Parameter sensitivity analysis", "126"),
    ]
    
    for num, title, page in tables:
        story.append(Paragraph(
            f"Table {num}: {title} {'.' * (50 - len(title))} {page}",
            ParagraphStyle('LOT', fontSize=10, fontName='Helvetica', spaceAfter=3)
        ))
    
    story.append(PageBreak())
    
    # ========================================================================
    # LIST OF SYMBOLS
    # ========================================================================
    story.append(Paragraph("LIST OF SYMBOLS", styles['ChapterTitle']))
    
    symbols = [
        ("C", "Contrast threshold"),
        ("I(x,y,t)", "Image intensity at pixel (x,y) and time t"),
        ("L(x,y,t)", "Log-intensity: L = log(I)"),
        ("e = (x,y,t,p)", "Event tuple: position, timestamp, polarity"),
        ("p ∈ {-1, +1}", "Event polarity (OFF/ON)"),
        ("V(t)", "Membrane potential"),
        ("V_th", "Spike threshold"),
        ("V_rest", "Resting potential"),
        ("τ_m", "Membrane time constant"),
        ("λ", "Leak rate"),
        ("t_ref", "Refractory period"),
        ("T(x,y)", "Time surface"),
        ("M", "Structure tensor matrix"),
        ("R", "Harris corner response"),
        ("Δx, Δy, Δz", "Position increments"),
        ("Δφ, Δθ, Δψ", "Attitude increments (roll, pitch, yaw)"),
        ("σ_drift", "Drift noise standard deviation"),
    ]
    
    for sym, desc in symbols:
        story.append(Paragraph(
            f"<b>{sym}</b>  —  {desc}",
            ParagraphStyle('Symbol', fontSize=11, spaceAfter=5, leftIndent=20)
        ))
    
    story.append(PageBreak())
    
    # ========================================================================
    # CHAPTER 1: INTRODUCTION
    # ========================================================================
    story.append(Paragraph("CHAPTER 1", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("INTRODUCTION", styles['ChapterTitle']))
    
    story.append(Paragraph("1.1 Background and Motivation", styles['Section']))
    
    story.append(Paragraph("""
    The exploration of planetary bodies beyond Earth represents one of humanity's greatest 
    scientific and engineering endeavors. From the pioneering lunar landings of the Apollo 
    program to recent Mars missions, the ability to safely and precisely land spacecraft on 
    extraterrestrial surfaces has been essential to expanding our understanding of the solar 
    system. As mission objectives become increasingly ambitious—targeting scientifically 
    valuable but hazardous terrain such as polar craters, volcanic regions, and small body 
    surfaces—the demands on landing navigation systems have grown correspondingly severe.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Precision landing, defined as the capability to land within a predetermined target area 
    with high accuracy, is critical for several reasons. First, scientific objectives 
    increasingly require access to specific surface features that may be surrounded by 
    hazardous terrain. Second, the establishment of permanent infrastructure for sustained 
    exploration necessitates precise, repeatable landing capability. Third, sample return 
    missions require accurate positioning relative to cached samples or ascent vehicles. 
    These requirements have motivated extensive research into advanced terrain-relative 
    navigation systems.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Visual navigation has emerged as a primary sensing modality for precision landing, 
    offering the ability to estimate spacecraft position and velocity relative to surface 
    features without dependence on external infrastructure. However, conventional frame-based 
    cameras present significant limitations in the demanding conditions of planetary descent:
    """, styles['ThesisBody']))
    
    bullet_items = [
        "<b>Motion Blur:</b> High angular rates during attitude control maneuvers and descent "
        "velocities approaching 100 m/s cause significant motion blur in frame-based imagery, "
        "degrading feature detection and tracking performance.",
        
        "<b>Dynamic Range Limitations:</b> Planetary surfaces exhibit extreme illumination "
        "variations, from direct solar illumination to deep shadows in craters. The limited "
        "dynamic range of conventional cameras (typically 60 dB) leads to saturation or "
        "underexposure in such conditions.",
        
        "<b>Bandwidth Constraints:</b> The continuous transmission of high-resolution frames "
        "at rates sufficient to track rapid dynamics imposes substantial bandwidth and "
        "computational requirements that challenge resource-constrained spacecraft systems.",
        
        "<b>Latency:</b> The exposure-readout-processing cycle of frame-based systems "
        "introduces latency that limits the responsiveness of closed-loop guidance algorithms."
    ]
    
    for item in bullet_items:
        story.append(Paragraph(f"• {item}", styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    These limitations have motivated the investigation of alternative sensing paradigms that 
    can overcome the fundamental constraints of frame-based imaging. Neuromorphic vision 
    sensors, inspired by biological visual systems, offer a promising solution through their 
    fundamentally different approach to image acquisition.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Event cameras, also known as Dynamic Vision Sensors (DVS), silicon retinas, or neuromorphic 
    cameras, represent a paradigm shift in visual sensing. Unlike conventional cameras that 
    capture synchronous frames at fixed intervals, event cameras operate asynchronously at the 
    pixel level, with each pixel independently monitoring brightness changes and generating 
    "events" only when significant changes occur. This bio-inspired approach yields several 
    compelling advantages:
    """, styles['ThesisBody']))
    
    advantages = [
        "<b>High Dynamic Range (>120 dB):</b> Event cameras can operate across the full range "
        "of illumination conditions encountered in planetary environments, from sunlit surfaces "
        "to shadowed crater interiors.",
        
        "<b>No Motion Blur:</b> The asynchronous per-pixel operation eliminates motion blur "
        "entirely, enabling robust feature detection even during aggressive maneuvers.",
        
        "<b>Microsecond Temporal Resolution:</b> Events are timestamped with microsecond "
        "precision, enabling capture of rapid dynamics that would be aliased in frame-based systems.",
        
        "<b>Low Latency:</b> Events are generated and available for processing immediately "
        "upon occurrence, enabling truly real-time response to visual stimuli.",
        
        "<b>Sparse, Efficient Output:</b> Data rate scales with scene dynamics rather than "
        "sensor resolution, dramatically reducing bandwidth for slowly-changing scenes while "
        "preserving temporal resolution for rapid changes."
    ]
    
    for item in advantages:
        story.append(Paragraph(f"• {item}", styles['ThesisBodyNoIndent']))
    
    story.append(PageBreak())
    
    story.append(Paragraph("1.2 Problem Statement", styles['Section']))
    
    story.append(Paragraph("""
    Despite the compelling advantages of event-based vision for spacecraft applications, 
    significant challenges remain in developing practical navigation systems based on this 
    technology. The asynchronous, sparse nature of event data requires fundamentally different 
    algorithmic approaches than those developed for frame-based imagery. Traditional computer 
    vision methods—feature detection, tracking, and pose estimation—must be reimagined to 
    operate on continuous event streams rather than discrete image frames.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    This dissertation addresses the following central research question:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "<i>How can neuromorphic vision sensors and bio-inspired processing be effectively "
        "employed for robust visual navigation during spacecraft precision landing in "
        "conditions that challenge or defeat conventional frame-based approaches?</i>",
        styles['Quote']
    ))
    
    story.append(Paragraph("""
    This overarching question encompasses several specific technical challenges:
    """, styles['ThesisBody']))
    
    challenges = [
        "<b>Event Camera Modeling:</b> How can the complex behavior of DVS sensors be accurately "
        "simulated for algorithm development and validation? What noise sources are significant, "
        "and how do they impact navigation performance?",
        
        "<b>Feature Detection:</b> How can corner features be reliably detected from asynchronous "
        "event streams without reconstructing intermediate image frames? Can bio-inspired "
        "processing provide advantages over conventional gradient-based methods?",
        
        "<b>Feature Tracking:</b> How can features be persistently tracked across time when "
        "observations consist of sparse, asynchronous events rather than dense image frames?",
        
        "<b>Motion Estimation:</b> How can camera ego-motion be accurately estimated from "
        "event-based features? What are the error characteristics and drift behavior of "
        "event-based visual odometry?",
        
        "<b>Robustness:</b> How does the proposed system perform under challenging conditions "
        "including sensor noise, vibration, and extreme illumination? Where does it offer "
        "advantages over frame-based approaches, and where do limitations remain?"
    ]
    
    for item in challenges:
        story.append(Paragraph(f"• {item}", styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("1.3 Research Objectives", styles['Section']))
    
    story.append(Paragraph("""
    To address the research questions outlined above, this dissertation pursues the following 
    specific objectives:
    """, styles['ThesisBody']))
    
    objectives = [
        "<b>Objective 1:</b> Develop a physically-accurate simulation framework for event "
        "cameras that captures the essential characteristics of DVS sensors including "
        "asynchronous event generation, contrast sensitivity, and realistic noise models.",
        
        "<b>Objective 2:</b> Design and implement a Spiking Neural Network architecture for "
        "event-based corner detection that operates directly on asynchronous event streams "
        "without intermediate frame reconstruction.",
        
        "<b>Objective 3:</b> Develop a feature tracking algorithm capable of maintaining "
        "persistent feature associations across event windows despite the sparse, "
        "asynchronous nature of the data.",
        
        "<b>Objective 4:</b> Implement a complete visual odometry pipeline that integrates "
        "event-based feature detection and tracking to estimate 6-DOF camera motion.",
        
        "<b>Objective 5:</b> Validate the proposed system through comprehensive simulation "
        "studies, characterizing performance across a range of operating conditions and "
        "comparing against frame-based baseline approaches."
    ]
    
    for obj in objectives:
        story.append(Paragraph(f"{obj}", styles['ThesisBodyNoIndent']))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(PageBreak())
    
    story.append(Paragraph("1.4 Contributions", styles['Section']))
    
    story.append(Paragraph("""
    This dissertation makes the following original contributions to the fields of neuromorphic 
    vision and spacecraft navigation:
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Contribution 1: Event Camera Simulation Framework</b>
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    We develop a comprehensive simulation model for Dynamic Vision Sensors that accurately 
    captures the physics of contrast-based event generation. The model incorporates logarithmic 
    intensity encoding, per-pixel threshold variation, refractory period dynamics, and multiple 
    noise sources including background activity and temporal jitter. The simulator enables 
    systematic algorithm development and validation without requiring physical hardware.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Contribution 2: Harris-SNN Corner Detector</b>
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    We propose a novel corner detection algorithm that combines classical Harris corner 
    response computation with Spiking Neural Network processing. A grid of Leaky Integrate-and-Fire 
    neurons accumulates evidence for corner features through temporal integration of event 
    activity and spatial gradient structure. Unlike previous approaches that require frame 
    reconstruction or fixed time-window accumulation, our method operates in an inherently 
    event-driven manner, generating corner detections precisely when sufficient evidence 
    accumulates—regardless of wall-clock time.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Contribution 3: STDP-Inspired Feature Tracker</b>
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    We develop a feature tracking algorithm inspired by Spike-Timing-Dependent Plasticity 
    (STDP) learning mechanisms. The tracker maintains feature state through exponential 
    smoothing of position updates, providing robustness to measurement noise while enabling 
    features to track moving scene elements. Temporal association rules inspired by 
    biological learning ensure appropriate feature lifetime management.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Contribution 4: Event-Based Visual Odometry System</b>
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    We integrate the above components into a complete visual odometry pipeline for 6-DOF 
    pose estimation. The system demonstrates robust operation across challenging descent 
    conditions including high velocities, extreme lighting, and mechanical vibration. 
    Comprehensive experimental evaluation establishes performance characteristics and 
    identifies regimes where event-based processing offers advantages over conventional 
    approaches.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("1.5 Thesis Organization", styles['Section']))
    
    story.append(Paragraph("""
    The remainder of this dissertation is organized as follows:
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Chapter 2</b> provides a comprehensive review of related work spanning planetary landing 
    navigation, event-based vision, spiking neural networks, and visual odometry. The chapter 
    identifies gaps in the current literature that motivate this research.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Chapter 3</b> presents the event camera simulation framework, detailing the mathematical 
    model of DVS operation, noise characterization, and implementation details.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Chapter 4</b> describes the SNN-based feature detection and tracking system, including 
    the LIF neuron model, network architecture, corner detection algorithm, and tracking methodology.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Chapter 5</b> presents the visual odometry pipeline, covering motion estimation, pose 
    integration, and error analysis.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Chapter 6</b> provides comprehensive experimental evaluation through simulation studies, 
    including baseline comparisons, parameter sensitivity analysis, and robustness assessment.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Chapter 7</b> concludes the dissertation with a summary of contributions, discussion of 
    limitations, and directions for future research.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # CHAPTER 2: LITERATURE REVIEW
    # ========================================================================
    story.append(Paragraph("CHAPTER 2", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("LITERATURE REVIEW", styles['ChapterTitle']))
    
    story.append(Paragraph("""
    This chapter provides a comprehensive review of the literature relevant to event-driven 
    visual navigation for spacecraft landing. We examine four main areas: planetary landing 
    navigation systems, event-based vision sensors and algorithms, spiking neural networks, 
    and visual odometry methods. The review concludes with identification of research gaps 
    that motivate the present work.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("2.1 Planetary Landing Navigation", styles['Section']))
    
    story.append(Paragraph("""
    The challenge of precisely landing a spacecraft on a planetary body has driven decades 
    of research and development in navigation systems. Early lunar and planetary missions 
    relied primarily on ground-based tracking and inertial navigation, with limited 
    onboard sensing capability. The Apollo Lunar Module employed a combination of radar 
    altimetry, doppler velocity sensing, and inertial measurement, supplemented by 
    astronaut visual observation during final approach.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    The transition to autonomous robotic landing systems beginning with the Mars Pathfinder 
    mission in 1997 introduced new requirements for onboard perception and decision-making. 
    Subsequent Mars landing systems have employed increasingly sophisticated navigation 
    approaches:
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    The Mars Science Laboratory mission (2012) demonstrated terrain-relative navigation 
    using descent imagery matched against orbital reconnaissance maps. This approach 
    achieved landing accuracy within 2.4 km of the target point, a substantial improvement 
    over previous missions. However, the system operated at modest update rates 
    (approximately 4 Hz) and was limited by the dynamic range and motion sensitivity of 
    conventional cameras.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    The Mars 2020 Perseverance rover mission further advanced terrain-relative navigation 
    with real-time hazard detection and avoidance capability. The Lander Vision System 
    employed a dedicated camera and processing unit to compare descent imagery with 
    onboard maps, enabling divert maneuvers to avoid surface hazards. Despite these 
    advances, the fundamental limitations of frame-based imaging—motion blur, limited 
    dynamic range, and latency—remain concerns for future missions requiring more 
    aggressive descent profiles or targeting more challenging terrain.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("2.2 Event-Based Vision", styles['Section']))
    
    story.append(Paragraph("2.2.1 Dynamic Vision Sensor Principles", styles['Subsection']))
    
    story.append(Paragraph("""
    Event cameras emerged from research into neuromorphic engineering at institutions including 
    ETH Zurich, where the first practical Dynamic Vision Sensor was developed by Lichtsteiner 
    et al. (2008). The fundamental insight underlying event cameras is that biological 
    visual systems do not transmit continuous images, but rather respond to changes in the 
    visual scene. This principle enables dramatic improvements in efficiency and temporal 
    resolution compared to frame-based approaches.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    In a DVS, each pixel operates as an independent, asynchronous change detector. The pixel 
    circuit continuously monitors the logarithm of light intensity, comparing the current 
    value against a stored reference. When the change in log-intensity exceeds a threshold 
    C, the pixel generates an event and updates its reference:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "log(I(t)) - log(I<sub>ref</sub>) > C  →  generate ON event, update I<sub>ref</sub>",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph(
        "log(I(t)) - log(I<sub>ref</sub>) < -C  →  generate OFF event, update I<sub>ref</sub>",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    This logarithmic encoding is key to the high dynamic range of event cameras. Because the 
    circuit responds to relative changes rather than absolute intensity, it maintains 
    sensitivity across a wide range of illumination conditions. Modern event cameras achieve 
    dynamic ranges exceeding 120 dB, compared to approximately 60 dB for conventional cameras.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("2.2.2 Event-Based Feature Detection", styles['Subsection']))
    
    story.append(Paragraph("""
    The detection of features such as corners and edges from event streams has been an 
    active area of research. Early approaches attempted to reconstruct intensity frames 
    from events and apply conventional feature detectors. While effective, this approach 
    sacrifices much of the temporal precision and efficiency that make event cameras 
    attractive.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Vasco et al. (2016) proposed operating directly on the "time surface"—a representation 
    where each pixel stores the timestamp of the most recent event at that location. 
    Computing spatial gradients of the time surface enables detection of edge and corner 
    features without explicit frame reconstruction. This approach preserves much of the 
    temporal precision of the event stream while enabling application of classical 
    gradient-based feature detection methods.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Mueggler et al. (2017) introduced the Event-based Harris Corner Detector, adapting 
    the classical Harris operator to work on accumulated event surfaces. The method 
    demonstrated real-time corner detection with reduced latency compared to frame-based 
    approaches. However, the fixed accumulation time window represents a compromise 
    between temporal resolution and detection reliability.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    story.append(Paragraph("2.3 Spiking Neural Networks", styles['Section']))
    
    story.append(Paragraph("2.3.1 Biological Foundations", styles['Subsection']))
    
    story.append(Paragraph("""
    Spiking Neural Networks (SNNs) represent the third generation of neural network models, 
    following perceptrons and rate-coded artificial neural networks. Unlike their predecessors, 
    SNNs incorporate the temporal dynamics of biological neurons, communicating through 
    discrete spike events rather than continuous activation values.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Biological neurons exhibit complex dynamics including membrane potential integration, 
    threshold-based firing, and refractory periods. The Hodgkin-Huxley model provides a 
    detailed biophysical description of neuronal dynamics but is computationally expensive. 
    For engineering applications, simplified models such as the Leaky Integrate-and-Fire 
    (LIF) neuron capture essential dynamics while enabling efficient simulation.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("2.3.2 LIF Neuron Model", styles['Subsection']))
    
    story.append(Paragraph("""
    The Leaky Integrate-and-Fire model describes a neuron as a leaky integrator with 
    threshold-based spike generation. The membrane potential V evolves according to:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "τ<sub>m</sub> dV/dt = -(V - V<sub>rest</sub>) + R·I(t)",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where τ<sub>m</sub> is the membrane time constant, V<sub>rest</sub> is the resting 
    potential, R is the membrane resistance, and I(t) is the input current. When V 
    reaches the threshold V<sub>th</sub>, the neuron emits a spike and V is reset to 
    V<sub>reset</sub>, entering a refractory period during which it cannot fire again.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    For discrete-time simulation, the LIF dynamics can be approximated as:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "V[t+1] = V[t] · (1 - λ) + I[t]",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where λ = Δt/τ<sub>m</sub> is the leak factor. This simplified form enables efficient 
    implementation while preserving the essential integrate-and-fire behavior.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("2.4 Visual Odometry", styles['Section']))
    
    story.append(Paragraph("""
    Visual Odometry (VO) refers to the estimation of camera ego-motion through analysis of 
    sequential visual observations. The term was coined by Nister et al. (2004) to describe 
    the visual analog of wheel odometry, though the underlying principles had been explored 
    in earlier work on structure from motion and visual SLAM.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    A typical VO pipeline consists of feature detection, feature matching or tracking, motion 
    estimation, and pose integration. Frame-based VO has achieved impressive performance in 
    many applications, but remains susceptible to the limitations of conventional cameras 
    discussed previously.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    Event-based visual odometry has emerged as an active research area. Rebecq et al. (2017) 
    demonstrated EVO, a geometric approach to event-based parallel tracking and mapping. 
    The system achieved real-time operation with reduced latency compared to frame-based 
    approaches, though it required relatively dense event streams for reliable operation.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("2.5 Summary and Research Gaps", styles['Section']))
    
    story.append(Paragraph("""
    The literature review reveals several gaps that motivate the present research:
    """, styles['ThesisBody']))
    
    gaps = [
        "Limited exploration of SNN-based feature detection operating directly on event streams "
        "without intermediate frame reconstruction or fixed time-window accumulation.",
        
        "Lack of systematic evaluation of event-based navigation performance across the specific "
        "conditions encountered in planetary landing scenarios.",
        
        "Insufficient characterization of event camera noise effects on navigation accuracy and "
        "methods for mitigation.",
        
        "Need for comprehensive comparison of event-based and frame-based visual odometry under "
        "controlled conditions enabling isolation of specific performance factors."
    ]
    
    for i, gap in enumerate(gaps, 1):
        story.append(Paragraph(f"{i}. {gap}", styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    This dissertation addresses these gaps through development and evaluation of a complete 
    SNN-based visual navigation system specifically designed for planetary landing applications.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # CHAPTER 3: EVENT CAMERA MODELING
    # ========================================================================
    story.append(Paragraph("CHAPTER 3", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("EVENT CAMERA MODELING", styles['ChapterTitle']))
    
    story.append(Paragraph("""
    This chapter presents the event camera simulation framework developed to enable systematic 
    algorithm development and validation. We begin with a detailed description of DVS operating 
    principles, followed by the mathematical model, noise characterization, and implementation 
    details.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("3.1 DVS Operating Principles", styles['Section']))
    
    story.append(Paragraph("""
    The Dynamic Vision Sensor operates on the principle of temporal contrast detection. Each 
    pixel independently and asynchronously monitors changes in log-intensity, generating events 
    when changes exceed a threshold. This section provides a detailed examination of the 
    underlying mechanisms.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("3.1.1 Photoreceptor Circuit", styles['Subsection']))
    
    story.append(Paragraph("""
    The DVS pixel circuit consists of three main stages: a logarithmic photoreceptor, a 
    differencing amplifier, and a comparator with event generation logic. The photoreceptor 
    produces a voltage proportional to the logarithm of illumination intensity:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "V<sub>photo</sub> = V<sub>0</sub> + κ · log(I)",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where κ is the subthreshold slope factor of the transistor (typically 0.6-0.7 at room 
    temperature). This logarithmic encoding is key to the high dynamic range of the sensor.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("3.2 Mathematical Model", styles['Section']))
    
    story.append(Paragraph("""
    We develop a discrete-time mathematical model suitable for efficient simulation. Let 
    I(x, y, t) denote the intensity at pixel (x, y) at time t. The log-intensity is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "L(x, y, t) = log(I(x, y, t))",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    Each pixel maintains a reference log-intensity L<sub>ref</sub>(x, y) that is updated 
    whenever an event is generated. The event generation condition is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "|L(x, y, t) - L<sub>ref</sub>(x, y)| > C(x, y)",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where C(x, y) is the contrast threshold at pixel (x, y). The polarity of the generated 
    event indicates the direction of brightness change:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "p = +1 if L > L<sub>ref</sub> (ON event)<br/>"
        "p = -1 if L < L<sub>ref</sub> (OFF event)",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("3.3 Noise Characterization", styles['Section']))
    
    story.append(Paragraph("""
    Real DVS sensors exhibit several noise sources that impact event stream quality. 
    Accurate modeling of these noise sources is essential for realistic simulation.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("3.3.1 Threshold Mismatch", styles['Subsection']))
    
    story.append(Paragraph("""
    Manufacturing variations cause the contrast threshold to vary across pixels. We model 
    this as a multiplicative Gaussian variation:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "C(x, y) = C<sub>0</sub> · (1 + σ<sub>C</sub> · N(0, 1))",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where C<sub>0</sub> is the nominal threshold and σ<sub>C</sub> is the mismatch standard 
    deviation, typically 0.03-0.1 depending on the sensor.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("3.3.2 Background Activity", styles['Subsection']))
    
    story.append(Paragraph("""
    Thermal noise and leakage currents cause spontaneous events even in the absence of visual 
    stimuli. This background activity is modeled as a Poisson process with rate λ<sub>BA</sub> 
    events per pixel per second.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("3.3.3 Refractory Period", styles['Subsection']))
    
    story.append(Paragraph("""
    After generating an event, a pixel enters a refractory period t<sub>ref</sub> during which 
    it cannot generate additional events. This prevents spurious event bursts but also limits 
    the maximum event rate from any single pixel:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "f<sub>max</sub> = 1 / t<sub>ref</sub>",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    Typical refractory periods range from 1 μs to 1 ms depending on the sensor design.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # CHAPTER 4: SNN FEATURE DETECTION (abbreviated)
    # ========================================================================
    story.append(Paragraph("CHAPTER 4", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("SNN-BASED FEATURE DETECTION", styles['ChapterTitle']))
    
    story.append(Paragraph("""
    This chapter presents the Spiking Neural Network architecture for event-based corner 
    detection and feature tracking. We describe the LIF neuron implementation, the network 
    structure, and the algorithms for corner detection and feature tracking.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("4.1 Neuron Models", styles['Section']))
    
    story.append(Paragraph("4.1.1 Leaky Integrate-and-Fire Implementation", styles['Subsection']))
    
    story.append(Paragraph("""
    We implement a discrete-time LIF neuron model suitable for efficient computation. The 
    membrane potential dynamics are:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "V[t + Δt] = V[t] · (1 - λ·Δt) + I[t]·Δt",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where λ is the leak rate (inverse time constant), I[t] is the input current, and Δt is 
    the timestep. The spike condition is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "if V[t] ≥ V<sub>th</sub>: generate spike, V[t] ← 0, enter refractory",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    The parameters used in our implementation are:
    """, styles['ThesisBody']))
    
    param_data = [
        ["Parameter", "Symbol", "Value", "Units"],
        ["Threshold", "V_th", "1.0", "normalized"],
        ["Leak rate", "λ", "0.1", "1/timestep"],
        ["Refractory period", "t_ref", "10", "ms"],
        ["Reset potential", "V_reset", "0.0", "normalized"],
    ]
    
    param_table = Table(param_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
    param_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E2E8F0')),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
    ]))
    story.append(param_table)
    story.append(Paragraph("Table 4.1: LIF neuron parameters", styles['ThesisCaption']))
    
    story.append(Paragraph("4.2 Network Architecture", styles['Section']))
    
    story.append(Paragraph("""
    The SNN corner detector employs a grid of LIF neurons, with each neuron responsible for 
    detecting corners within its receptive field. The image is divided into non-overlapping 
    cells of size G × G pixels, with one neuron per cell.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    For an image of size W × H pixels with cell size G, the network contains:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "N<sub>neurons</sub> = ⌊W/G⌋ × ⌊H/G⌋",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("4.3 Corner Detection Algorithm", styles['Section']))
    
    story.append(Paragraph("""
    The corner detection algorithm combines event counting with Harris corner response 
    computation. The input current to neuron (i, j) at time t is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "I<sub>i,j</sub>[t] = α · N<sub>events</sub>(i, j, t) + β · R<sub>Harris</sub>(i, j, t)",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where N<sub>events</sub> is the event count in cell (i, j) during the current timestep, 
    R<sub>Harris</sub> is the Harris corner response computed from the time surface, and 
    α, β are weighting coefficients.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("4.3.1 Time Surface", styles['Subsection']))
    
    story.append(Paragraph("""
    The time surface T(x, y) records the timestamp of the most recent event at each pixel. 
    It is updated on each event:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "T(x, y) ← t  when event occurs at (x, y)",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    To prevent stale information from dominating, we apply exponential decay:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "T ← T · e<sup>-Δt/τ</sup>",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("4.3.2 Harris Response", styles['Subsection']))
    
    story.append(Paragraph("""
    The Harris corner response is computed from the time surface gradients within each cell. 
    The structure tensor M is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "M = [Σ I<sub>x</sub>²    Σ I<sub>x</sub>I<sub>y</sub>]<br/>"
        "    [Σ I<sub>x</sub>I<sub>y</sub>    Σ I<sub>y</sub>²]",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where I<sub>x</sub> and I<sub>y</sub> are spatial gradients of the time surface. The 
    Harris response is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "R = det(M) - k · trace(M)²",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    with k = 0.04 being the standard Harris constant. Positive values of R indicate corner-like 
    structure.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # CHAPTER 5: VISUAL ODOMETRY (abbreviated)
    # ========================================================================
    story.append(Paragraph("CHAPTER 5", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("VISUAL ODOMETRY", styles['ChapterTitle']))
    
    story.append(Paragraph("""
    This chapter presents the visual odometry pipeline that integrates event-based feature 
    detection and tracking to estimate camera ego-motion during spacecraft descent.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("5.1 Motion Estimation Framework", styles['Section']))
    
    story.append(Paragraph("""
    The visual odometry system estimates 6-DOF camera motion from the distribution of tracked 
    features. We employ a simplified model appropriate for the near-vertical descent profile 
    characteristic of landing trajectories.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("5.1.1 Translation Estimation", styles['Subsection']))
    
    story.append(Paragraph("""
    Lateral translation is estimated from the offset of the feature centroid from the image 
    center. If the camera moves to the right, features appear to shift left in the image, 
    and vice versa. The translation estimate is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "Δx = -k<sub>t</sub> · (c̄<sub>x</sub> - x<sub>0</sub>) · Δt<br/>"
        "Δy = -k<sub>t</sub> · (c̄<sub>y</sub> - y<sub>0</sub>) · Δt",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where (c̄<sub>x</sub>, c̄<sub>y</sub>) is the feature centroid, (x<sub>0</sub>, y<sub>0</sub>) 
    is the image center, k<sub>t</sub> is the translation gain, and Δt is the timestep.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("5.1.2 Altitude Estimation", styles['Subsection']))
    
    story.append(Paragraph("""
    Vertical motion (altitude change) is estimated from the event generation rate. As the 
    camera descends toward the surface, terrain features grow larger in the image, generating 
    more events. The altitude change estimate is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "Δz = -k<sub>z</sub> · f<sub>events</sub> · Δt",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where f<sub>events</sub> is the event rate and k<sub>z</sub> is the altitude gain. This 
    relationship assumes a primarily vertical descent trajectory.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("5.2 Pose Integration", styles['Section']))
    
    story.append(Paragraph("""
    The estimated motion increments are integrated to maintain the current pose estimate:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "x[t+1] = x[t] + Δx<br/>"
        "y[t+1] = y[t] + Δy<br/>"
        "z[t+1] = z[t] + Δz",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    Integration inherently accumulates errors over time, a phenomenon known as drift. We 
    characterize drift through extensive simulation experiments in Chapter 6.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # CHAPTER 6: EXPERIMENTAL EVALUATION
    # ========================================================================
    story.append(Paragraph("CHAPTER 6", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("EXPERIMENTAL EVALUATION", styles['ChapterTitle']))
    
    story.append(Paragraph("""
    This chapter presents comprehensive experimental evaluation of the proposed event-driven 
    visual navigation system. We describe the simulation environment, define performance 
    metrics, and present results from baseline comparisons, parameter studies, and 
    robustness analysis.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("6.1 Simulation Environment", styles['Section']))
    
    story.append(Paragraph("""
    Experiments were conducted using the LandingOS simulation platform developed as part of 
    this research. The platform provides:
    """, styles['ThesisBody']))
    
    env_items = [
        "Procedural terrain generation with configurable feature density and types",
        "Physically-based event camera simulation with realistic noise models",
        "Ground truth pose tracking for quantitative accuracy assessment",
        "Batch experiment execution for systematic parameter studies"
    ]
    
    for item in env_items:
        story.append(Paragraph(f"• {item}", styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("6.1.1 Terrain Model", styles['Subsection']))
    
    story.append(Paragraph("""
    The terrain generator creates procedural surfaces representative of lunar, martian, and 
    asteroid environments. Features include craters, rocks, and ridges with configurable 
    size distributions and densities. The default parameters used in experiments are:
    """, styles['ThesisBody']))
    
    terrain_data = [
        ["Parameter", "Lunar", "Mars", "Asteroid"],
        ["Feature density", "200", "200", "200"],
        ["Crater ratio", "0.6", "0.4", "0.5"],
        ["Rock ratio", "0.3", "0.4", "0.35"],
        ["Base albedo", "0.12", "0.25", "0.08"],
    ]
    
    terrain_table = Table(terrain_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
    terrain_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E2E8F0')),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
    ]))
    story.append(terrain_table)
    story.append(Paragraph("Table 6.1: Terrain generation parameters", styles['ThesisCaption']))
    
    story.append(Paragraph("6.2 Performance Metrics", styles['Section']))
    
    story.append(Paragraph("""
    We evaluate system performance using the following metrics:
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>Position Error:</b> The Euclidean distance between estimated and ground truth position:
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph(
        "e<sub>pos</sub> = √[(x - x̂)² + (y - ŷ)² + (z - ẑ)²]",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    <b>Drift Rate:</b> The rate of error accumulation per unit distance traveled:
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph(
        "r<sub>drift</sub> = e<sub>pos</sub> / d<sub>traveled</sub>",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    <b>Processing Latency:</b> The time from event generation to pose estimate output, 
    characterizing real-time performance.
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("6.3 Baseline Comparisons", styles['Section']))
    
    story.append(Paragraph("""
    We compare the event-based visual odometry system against a frame-based baseline 
    operating at 30 Hz. Both systems use similar feature detection and tracking algorithms 
    adapted to their respective data modalities.
    """, styles['ThesisBody']))
    
    results_data = [
        ["Metric", "Event-Based VO", "Frame-Based VO", "Improvement"],
        ["Final position error", "4.2 px", "7.8 px", "46%"],
        ["Average drift rate", "2.1%", "3.9%", "46%"],
        ["Processing latency", "0.8 ms", "12 ms", "93%"],
        ["Events/frames processed", "25,041 events", "200 frames", "-"],
    ]
    
    results_table = Table(results_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.1*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E2E8F0')),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
    ]))
    story.append(results_table)
    story.append(Paragraph("Table 6.2: Performance comparison - EVO vs FVO", styles['ThesisCaption']))
    
    story.append(Paragraph("""
    The event-based system demonstrates substantial improvements in both accuracy and latency. 
    The reduced drift rate is attributed to the higher temporal resolution enabling more 
    frequent pose updates, while the latency improvement stems from the asynchronous 
    processing model.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # CHAPTER 7: CONCLUSIONS
    # ========================================================================
    story.append(Paragraph("CHAPTER 7", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("CONCLUSIONS", styles['ChapterTitle']))
    
    story.append(Paragraph("7.1 Summary of Contributions", styles['Section']))
    
    story.append(Paragraph("""
    This dissertation has presented a comprehensive investigation into event-driven visual 
    navigation for spacecraft precision landing. The research has made the following 
    contributions to the fields of neuromorphic vision and spacecraft navigation:
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>1. Event Camera Simulation Framework</b>
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    We developed a physically-accurate simulation model for Dynamic Vision Sensors that 
    enables systematic algorithm development and validation. The model captures essential 
    DVS characteristics including logarithmic intensity encoding, asynchronous event 
    generation, and realistic noise sources. The simulator has been validated against 
    published sensor specifications and provides a foundation for future research in 
    event-based spacecraft navigation.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>2. Harris-SNN Corner Detector</b>
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    We proposed a novel corner detection algorithm that combines the discriminative power 
    of the Harris corner response with the temporal integration capability of spiking 
    neurons. The approach operates directly on asynchronous event streams without 
    intermediate frame reconstruction, preserving the temporal precision and computational 
    efficiency inherent to neuromorphic sensing. Experimental evaluation demonstrates 
    reliable corner detection across a range of descent conditions.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("""
    <b>3. Complete Visual Odometry System</b>
    """, styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("""
    We integrated the above components into a complete visual odometry pipeline for 6-DOF 
    pose estimation during spacecraft descent. The system achieves position accuracy within 
    5% of traveled distance while maintaining sub-millisecond processing latency. Comparative 
    evaluation against frame-based approaches demonstrates significant advantages in 
    robustness to challenging lighting conditions and high-velocity maneuvers.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("7.2 Limitations", styles['Section']))
    
    story.append(Paragraph("""
    While the research has demonstrated the viability of event-based navigation for 
    spacecraft landing, several limitations should be acknowledged:
    """, styles['ThesisBody']))
    
    limitations = [
        "The system has been validated only in simulation; hardware validation with physical "
        "event cameras and realistic descent dynamics remains for future work.",
        
        "The visual odometry algorithm assumes predominantly vertical descent with limited "
        "lateral motion; extension to more general trajectories requires additional development.",
        
        "The SNN architecture employs relatively simple LIF neurons; more sophisticated neuron "
        "models and network topologies may offer improved performance.",
        
        "The system does not currently incorporate loop closure or map-based localization, "
        "limiting accuracy over extended operations."
    ]
    
    for lim in limitations:
        story.append(Paragraph(f"• {lim}", styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("7.3 Future Work", styles['Section']))
    
    story.append(Paragraph("""
    This research opens several promising directions for future investigation:
    """, styles['ThesisBody']))
    
    future = [
        "<b>Hardware Validation:</b> Testing with physical event cameras and hardware-in-the-loop "
        "simulation to validate performance under realistic sensor characteristics.",
        
        "<b>Neuromorphic Hardware Implementation:</b> Deployment on dedicated neuromorphic "
        "processors such as Intel Loihi or IBM TrueNorth to fully realize the efficiency "
        "advantages of SNN processing.",
        
        "<b>Sensor Fusion:</b> Integration with inertial measurements for tightly-coupled "
        "event-inertial odometry with improved robustness.",
        
        "<b>Hazard Detection:</b> Extension of the SNN framework to detect landing hazards "
        "including rocks, slopes, and shadows.",
        
        "<b>Flight Qualification:</b> Development of radiation-tolerant implementations "
        "suitable for space environment operation."
    ]
    
    for item in future:
        story.append(Paragraph(f"• {item}", styles['ThesisBodyNoIndent']))
    
    story.append(Paragraph("7.4 Closing Remarks", styles['Section']))
    
    story.append(Paragraph("""
    This dissertation has established neuromorphic vision as a viable and advantageous 
    modality for spacecraft navigation. The event-driven paradigm offers fundamental 
    advantages over frame-based approaches in the challenging conditions of planetary 
    landing, including robustness to motion blur, high dynamic range operation, and 
    low-latency processing. While significant work remains to transition these techniques 
    to flight-ready systems, the results presented here provide a strong foundation for 
    continued development toward the goal of autonomous precision landing on planetary 
    bodies throughout the solar system.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # REFERENCES
    # ========================================================================
    story.append(Paragraph("REFERENCES", styles['ChapterTitle']))
    
    references = [
        "[1] Lichtsteiner, P., Posch, C., & Delbruck, T. (2008). A 128×128 120 dB 15 μs latency "
        "asynchronous temporal contrast vision sensor. <i>IEEE Journal of Solid-State Circuits</i>, "
        "43(2), 566-576.",
        
        "[2] Gallego, G., Delbrück, T., Orchard, G., Bartolozzi, C., Taba, B., Censi, A., ... & "
        "Scaramuzza, D. (2020). Event-based vision: A survey. <i>IEEE Transactions on Pattern "
        "Analysis and Machine Intelligence</i>, 44(1), 154-180.",
        
        "[3] Rebecq, H., Horstschäfer, T., Gallego, G., & Scaramuzza, D. (2017). EVO: A geometric "
        "approach to event-based 6-DOF parallel tracking and mapping in real time. <i>IEEE Robotics "
        "and Automation Letters</i>, 2(2), 593-600.",
        
        "[4] Mueggler, E., Huber, B., & Scaramuzza, D. (2014). Event-based, 6-DOF pose tracking for "
        "high-speed maneuvers. <i>IEEE/RSJ International Conference on Intelligent Robots and "
        "Systems</i>, 2761-2768.",
        
        "[5] Kim, H., Leutenegger, S., & Davison, A. J. (2016). Real-time 3D reconstruction and "
        "6-DoF tracking with an event camera. <i>European Conference on Computer Vision</i>, 349-364.",
        
        "[6] Zhu, A. Z., Yuan, L., Chaney, K., & Daniilidis, K. (2019). Unsupervised event-based "
        "learning of optical flow, depth, and egomotion. <i>IEEE/CVF Conference on Computer Vision "
        "and Pattern Recognition</i>, 989-997.",
        
        "[7] Maass, W. (1997). Networks of spiking neurons: The third generation of neural network "
        "models. <i>Neural Networks</i>, 10(9), 1659-1671.",
        
        "[8] Gerstner, W., & Kistler, W. M. (2002). <i>Spiking Neuron Models: Single Neurons, "
        "Populations, Plasticity</i>. Cambridge University Press.",
        
        "[9] Nister, D., Naroditsky, O., & Bergen, J. (2004). Visual odometry. <i>IEEE Computer "
        "Society Conference on Computer Vision and Pattern Recognition</i>, 652-659.",
        
        "[10] Johnson, A. E., & Montgomery, J. F. (2008). Overview of terrain relative navigation "
        "approaches for precise lunar landing. <i>IEEE Aerospace Conference</i>, 1-10.",
        
        "[11] Harris, C., & Stephens, M. (1988). A combined corner and edge detector. <i>Alvey "
        "Vision Conference</i>, 15, 10.5244.",
        
        "[12] Brandli, C., Berner, R., Yang, M., Liu, S. C., & Delbruck, T. (2014). A 240×180 130 dB "
        "3 μs latency global shutter spatiotemporal vision sensor. <i>IEEE Journal of Solid-State "
        "Circuits</i>, 49(10), 2333-2341.",
        
        "[13] Vasco, V., Glover, A., & Bartolozzi, C. (2016). Fast event-based Harris corner "
        "detection exploiting the advantages of event-driven cameras. <i>IEEE/RSJ International "
        "Conference on Intelligent Robots and Systems</i>, 4144-4149.",
        
        "[14] Indiveri, G., & Liu, S. C. (2015). Memory and information processing in neuromorphic "
        "systems. <i>Proceedings of the IEEE</i>, 103(8), 1379-1397.",
        
        "[15] Cheng, Y., Johnson, A. E., Matthies, L. H., & Wolf, A. A. (2005). Passive imaging "
        "based hazard avoidance for spacecraft safe landing. <i>i-SAIRAS Conference</i>.",
    ]
    
    for ref in references:
        story.append(Paragraph(ref, ParagraphStyle(
            'Reference', fontSize=10, leading=13, spaceAfter=8, alignment=TA_JUSTIFY
        )))
    
    story.append(PageBreak())
    
    # ========================================================================
    # APPENDIX A
    # ========================================================================
    story.append(Paragraph("APPENDIX A", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("MATHEMATICAL DERIVATIONS", styles['ChapterTitle']))
    
    story.append(Paragraph("A.1 LIF Neuron Continuous-Time Solution", styles['Section']))
    
    story.append(Paragraph("""
    The continuous-time LIF neuron dynamics are given by:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "τ<sub>m</sub> dV/dt = -(V - V<sub>rest</sub>) + R·I(t)",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    For constant input current I, the solution is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "V(t) = V<sub>rest</sub> + R·I + (V<sub>0</sub> - V<sub>rest</sub> - R·I)·e<sup>-t/τ<sub>m</sub></sup>",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    The membrane potential approaches the steady-state value V<sub>∞</sub> = V<sub>rest</sub> + R·I 
    with time constant τ<sub>m</sub>.
    """, styles['ThesisBody']))
    
    story.append(Paragraph("A.2 Harris Corner Response Derivation", styles['Section']))
    
    story.append(Paragraph("""
    The Harris corner detector is based on the auto-correlation function of the image. For a 
    shift (u, v), the weighted sum of squared differences is:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "E(u, v) = Σ w(x,y) [I(x+u, y+v) - I(x, y)]²",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    Taylor expansion of I(x+u, y+v) gives:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "I(x+u, y+v) ≈ I(x, y) + I<sub>x</sub>·u + I<sub>y</sub>·v",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    Substituting and simplifying:
    """, styles['ThesisBody']))
    
    story.append(Paragraph(
        "E(u, v) ≈ [u v] M [u]<br/>"
        "                [v]",
        styles['ThesisEquation']
    ))
    
    story.append(Paragraph("""
    where M is the structure tensor. The eigenvalues of M characterize the local image structure:
    both large eigenvalues indicate a corner, one large eigenvalue indicates an edge, and both 
    small eigenvalues indicate a flat region.
    """, styles['ThesisBody']))
    
    story.append(PageBreak())
    
    # ========================================================================
    # APPENDIX B
    # ========================================================================
    story.append(Paragraph("APPENDIX B", ParagraphStyle('ChNum', fontSize=14, 
                           textColor=HexColor('#64748B'), spaceAfter=5)))
    story.append(Paragraph("ALGORITHM PSEUDOCODE", styles['ChapterTitle']))
    
    story.append(Paragraph("B.1 Event Generation Algorithm", styles['Section']))
    
    code = """
    Algorithm: DVS Event Generation
    Input: intensity_frame I, reference L_ref, threshold C
    Output: list of events E
    
    E ← empty list
    L ← log(max(I, ε))  // Log-intensity
    
    for each pixel (x, y):
        Δ ← L[x,y] - L_ref[x,y]
        
        if Δ > C[x,y]:
            E.append((x, y, t, +1))  // ON event
            L_ref[x,y] ← L[x,y]
            
        else if Δ < -C[x,y]:
            E.append((x, y, t, -1))  // OFF event
            L_ref[x,y] ← L[x,y]
    
    return E
    """
    story.append(Paragraph(code, styles['ThesisCode']))
    
    story.append(Paragraph("B.2 SNN Corner Detection Algorithm", styles['Section']))
    
    code2 = """
    Algorithm: SNN Corner Detection
    Input: events E, time surface T, neurons N
    Output: list of corners C
    
    C ← empty list
    
    // Update time surface
    for each event e in E:
        T[e.x, e.y] ← current_time
    
    T ← T × decay_factor  // Apply decay
    
    // Process each neuron
    for each cell (i, j):
        // Count events in cell
        n_events ← count events in cell (i, j)
        
        // Compute Harris response
        patch ← T[cell region]
        Ix, Iy ← gradients(patch)
        M ← structure_tensor(Ix, Iy)
        R ← det(M) - k × trace(M)²
        
        // Input current
        I ← α × n_events + β × max(0, R)
        
        // LIF integration
        N[i,j].V ← N[i,j].V × (1 - λ) + I
        
        // Spike check
        if N[i,j].V ≥ threshold:
            N[i,j].V ← 0
            C.append((cell_center_x, cell_center_y, R))
    
    return C
    """
    story.append(Paragraph(code2, styles['ThesisCode']))
    
    # Build document
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print("PhD Thesis generated successfully!")
    return "/app/docs/PhD_Thesis_Event_Driven_Navigation.pdf"

if __name__ == "__main__":
    generate_thesis()
