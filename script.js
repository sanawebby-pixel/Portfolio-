document.addEventListener('DOMContentLoaded', () => {
    
    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ==========================================================================
       1 & 2 & 3. NAVBAR LOGIC (Mobile Menu, Sticky, Active State)
       ========================================================================== */
    const navbar = document.getElementById('navbar');
    const hamburger = document.querySelector('.hamburger');
    const navLinksContainer = document.querySelector('.nav-links');
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section');

    // Toggle mobile menu
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navLinksContainer.classList.toggle('active');
    });

    // Close mobile menu when a link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navLinksContainer.classList.remove('active');
        });
    });

    // Sticky Navbar & Active Section tracking on scroll
    window.addEventListener('scroll', () => {
        // Sticky navbar
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Active section logic
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (window.scrollY >= (sectionTop - sectionHeight / 3)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });

    /* ==========================================================================
       5. SCROLL REVEAL ANIMATIONS (Intersection Observer)
       ========================================================================== */
    if (!prefersReducedMotion) {
        const revealOptions = {
            threshold: 0.15,
            rootMargin: "0px 0px -50px 0px"
        };

        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    observer.unobserve(entry.target); // Reveal only once
                }
            });
        }, revealOptions);

        document.querySelectorAll('.reveal, .reveal-right, .reveal-stagger').forEach(element => {
            revealObserver.observe(element);
        });
    }

    /* ==========================================================================
       6. PARTICLE.JS INITIALIZATION (tsParticles)
       ========================================================================== */
    // Determine density based on screen width for performance
    let particleDensity = 80;
    if (window.innerWidth <= 768) {
        particleDensity = 40; // Tablet
    }
    if (window.innerWidth <= 480) {
        particleDensity = 20; // Mobile
    }
    if (prefersReducedMotion) {
        particleDensity = 0; // Disable particles if reduced motion is requested
    }

    if (particleDensity > 0 && typeof tsParticles !== 'undefined') {
        tsParticles.load("tsparticles", {
            fpsLimit: 60,
            interactivity: {
                events: {
                    onClick: { enable: true, mode: "push" },
                    onHover: { enable: true, mode: "grab" },
                    resize: true
                },
                modes: {
                    push: { quantity: 4 },
                    grab: { distance: 140, links: { opacity: 0.5 } }
                }
            },
            particles: {
                color: { value: ["#00F0FF", "#8B5CF6", "#1E40AF"] },
                links: {
                    color: "#ffffff",
                    distance: 150,
                    enable: true,
                    opacity: 0.1,
                    width: 1
                },
                collisions: { enable: false },
                move: {
                    direction: "none",
                    enable: true,
                    outModes: { default: "bounce" },
                    random: false,
                    speed: 0.8,
                    straight: false
                },
                number: {
                    density: { enable: true, area: 800 },
                    value: particleDensity
                },
                opacity: {
                    value: 0.3,
                    animation: { enable: true, minimumValue: 0.1, speed: 1, sync: false }
                },
                shape: { type: "circle" },
                size: {
                    value: { min: 1, max: 3 },
                    animation: { enable: true, minimumValue: 1, speed: 2, sync: false }
                }
            },
            detectRetina: true
        });
    }

    /* ==========================================================================
       7 & 8. CUSTOM CURSOR
       ========================================================================== */
    const cursorDot = document.querySelector('.cursor-dot');
    const cursorRing = document.querySelector('.cursor-ring');
    
    // Check if it's a touch device
    const isTouchDevice = (('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (navigator.msMaxTouchPoints > 0));

    if (!isTouchDevice && !prefersReducedMotion && cursorDot && cursorRing) {
        let mouseX = 0;
        let mouseY = 0;
        let ringX = 0;
        let ringY = 0;

        window.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            
            // Move dot instantly
            cursorDot.style.left = `${mouseX}px`;
            cursorDot.style.top = `${mouseY}px`;
        });

        // Smooth follow for ring using requestAnimationFrame
        const renderCursor = () => {
            // Easing
            ringX += (mouseX - ringX) * 0.15;
            ringY += (mouseY - ringY) * 0.15;
            
            cursorRing.style.left = `${ringX}px`;
            cursorRing.style.top = `${ringY}px`;
            
            requestAnimationFrame(renderCursor);
        };
        requestAnimationFrame(renderCursor);

        // Hover effects
        const interactiveElements = document.querySelectorAll('a, button, input, textarea, .magnetic-btn');
        
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                document.body.classList.add('cursor-hover');
            });
            el.addEventListener('mouseleave', () => {
                document.body.classList.remove('cursor-hover');
            });
        });
    }

    /* ==========================================================================
       9. MAGNETIC BUTTONS
       ========================================================================== */
    if (!isTouchDevice && !prefersReducedMotion) {
        const magneticButtons = document.querySelectorAll('.magnetic-btn');
        
        magneticButtons.forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const position = btn.getBoundingClientRect();
                const x = e.clientX - position.left - position.width / 2;
                const y = e.clientY - position.top - position.height / 2;
                
                btn.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = `translate(0px, 0px)`;
            });
        });
    }

    /* ==========================================================================
       10. SKILL FILTERING
       ========================================================================== */
    const filterBtns = document.querySelectorAll('.filter-btn');
    const skillCards = document.querySelectorAll('.skill-card');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            filterBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');

            const filter = btn.getAttribute('data-filter');

            skillCards.forEach(card => {
                if (filter === 'all') {
                    card.classList.remove('hidden');
                    // Small timeout to allow transition if we wanted to animate display
                    setTimeout(() => { card.style.opacity = '1'; }, 50);
                } else {
                    if (card.getAttribute('data-category') === filter) {
                        card.classList.remove('hidden');
                        setTimeout(() => { card.style.opacity = '1'; }, 50);
                    } else {
                        card.style.opacity = '0';
                        setTimeout(() => { card.classList.add('hidden'); }, 300); // Wait for fade out
                    }
                }
            });
        });
    });

    /* ==========================================================================
       11. CONTACT FORM VALIDATION
       ========================================================================== */
    const contactForm = document.getElementById('contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            let isValid = true;
            
            const nameInput = document.getElementById('name');
            const emailInput = document.getElementById('email');
            const messageInput = document.getElementById('message');
            const successMsg = document.querySelector('.form-success');
            
            // Validate Name
            if (!nameInput.value.trim()) {
                nameInput.parentElement.classList.add('error');
                isValid = false;
            } else {
                nameInput.parentElement.classList.remove('error');
            }
            
            // Validate Email (Basic Regex)
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailInput.value.trim() || !emailRegex.test(emailInput.value)) {
                emailInput.parentElement.classList.add('error');
                isValid = false;
            } else {
                emailInput.parentElement.classList.remove('error');
            }
            
            // Validate Message
            if (!messageInput.value.trim()) {
                messageInput.parentElement.classList.add('error');
                isValid = false;
            } else {
                messageInput.parentElement.classList.remove('error');
            }
            
            if (isValid) {
                // Simulate sending message
                const btnSpan = contactForm.querySelector('.submit-btn span');
                const originalText = btnSpan.textContent;
                btnSpan.textContent = 'SENDING...';
                
                setTimeout(() => {
                    successMsg.style.display = 'block';
                    contactForm.reset();
                    btnSpan.textContent = originalText;
                    
                    // Hide success message after 5 seconds
                    setTimeout(() => {
                        successMsg.style.display = 'none';
                    }, 5000);
                }, 1500);
            }
        });

        // Remove error styling on input
        const inputs = contactForm.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                input.parentElement.classList.remove('error');
            });
        });
    }

    /* ==========================================================================
       12. SCROLL-TO-TOP BUTTON
       ========================================================================== */
    const scrollTopBtn = document.getElementById('scrollToTop');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    });
    
    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    /* ==========================================================================
       13. DYNAMIC FOOTER YEAR
       ========================================================================== */
    const yearElement = document.getElementById('current-year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
});
