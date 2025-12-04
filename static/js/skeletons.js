document.addEventListener('DOMContentLoaded', function() {
  // Replace product images with a skeleton until they load
  const productImages = document.querySelectorAll('img.product-image, img.img-fluid');
  productImages.forEach(img => {
    // Skip images without a src
    if (!img.src) return;
    // Create skeleton overlay
    const wrapper = document.createElement('div');
    wrapper.className = 'skeleton-wrapper';
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-card';
    // Insert wrapper before img
    img.parentNode.insertBefore(wrapper, img);
    wrapper.appendChild(img);
    wrapper.insertBefore(skeleton, img);

    // When image loads, remove skeleton
    if (img.complete && img.naturalWidth !== 0) {
      skeleton.style.display = 'none';
    } else {
      img.addEventListener('load', function() {
        skeleton.style.display = 'none';
      });
      img.addEventListener('error', function() {
        skeleton.style.display = 'none';
      });
    }
  });
});
