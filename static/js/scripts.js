// Add interactivity here (e.g., carousel autoplay)
document.addEventListener('DOMContentLoaded', function () {
    const carousel = new bootstrap.Carousel('#trendingCarousel', {
        interval: 3000,  // Rotate every 3 seconds
        wrap: true
    });
});