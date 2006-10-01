# This file contains some miscellanious displayables that involve images.
# Most of the guts of this file have been moved into im.py, with only some
# of the stuff thar uses images remaining.

import renpy
from renpy.display.render import render

import pygame
from pygame.constants import *

Image = renpy.display.im.image

class UncachedImage(renpy.display.core.Displayable):
    """
    An image that is loaded immediately and not cached.
    """

    def __init__(self, file, hint=None, scale=None, style='image_placement',
                 **properties):

        super(UncachedImage, self).__init__()

        self.surf = pygame.image.load(file, hint)
        self.surf = self.surf.convert_alpha()

        if scale:
            self.surf = pygame.transform.scale(self.surf, scale)

        renpy.display.render.mutated_surface(self.surf)

        self.style = renpy.style.Style(style, properties)

    def render(self, w, h, st, at):
        sw, sh = self.surf.get_size()
        rv = renpy.display.render.Render(sw, sh)
        rv.blit(self.surf, (0, 0))

        return rv


class ImageReference(renpy.display.core.Displayable):
    """
    ImageReference objects are used to reference images by their name,
    which is a tuple of strings corresponding to the name used to define
    the image in an image statment.
    """

    nosave = [ 'target' ]
    target = None

    def __init__(self, name, **properties):
        """
        @param name: A tuple of strings, the name of the image. Or else
        a displayable, containing the image directly.
        """
        
        super(ImageReference, self).__init__(**properties)

        self.name = name

    def find_target(self):
        import renpy.exports as exports

        name = self.name

        if isinstance(name, renpy.display.core.Displayable):
            self.target = name
            return

        
        parameters = [ ]

        def error(msg):
            self.target = renpy.display.text.Text(msg, color=(255, 0, 0, 255), xanchor=0, xpos=0, yanchor=0, ypos=0)

            if renpy.config.debug:
                raise Exception(msg)

            
        # Scan through, searching for an image (defined with an
        # input statement) that is a prefix of the given name.
        while name:
            if name in exports.images:
                target = exports.images[name]

                try:
                    self.target = target.parameterize(name, parameters)
                except Exception, e:
                    if renpy.config.debug:
                        raise

                    error(str(e))

                return

            else:
                parameters.insert(0, name[-1])
                name = name[:-1]

        error("Image '%s' not found." % ' '.join(self.name))
        

    def event(self, ev, x, y, st):
        if not self.target:
            self.find_target()

        return self.target.event(ev, x, y, st)
        
    def render(self, width, height, st, at):
        if not self.target:
            self.find_target()

        return render(self.target, width, height, st, at)

    def get_placement(self):
        if not self.target:
            self.find_target()

        xpos, ypos, xanchor, yanchor = self.target.get_placement()
        
        if xpos is None:
            xpos = self.style.xpos

        if ypos is None:
            ypos = self.style.ypos

        if xanchor is None:
            xanchor = self.style.xanchor

        if yanchor is None:
            yanchor = self.style.yanchor

        return xpos, ypos, xanchor, yanchor

    def visit(self):
        if not self.target:
            self.find_target()

        return [ self.target ]
    
    
class Solid(renpy.display.core.Displayable):
    """
    Returns a Displayable that is solid, and filled with a single
    color. A Solid expands to fill all the space allocated to it,
    making it suitable for use as a background.
    """

    def __init__(self, color):
        """
        @param color: An RGBA tuple, giving the color that the display
        will be filled with.
        """
        
        super(Solid, self).__init__()
        self.color = renpy.easy.color(color)

    def render(self, width, height, st, at):

        si = renpy.display.im.SolidImage(self.color,
                                         width,
                                         height)

        return render(si, width, height, st, at)
        
class Frame(renpy.display.core.Displayable):
    """
    Returns a Displayable that is a frame, based on the supplied image
    filename. A frame is an image that is automatically rescaled to
    the size allocated to it. The image has borders that are only
    scaled in one axis. The region within xborder pixels of the left
    and right borders is only scaled in the y direction, while the
    region within yborder pixels of the top and bottom axis is scaled
    only in the x direction. The corners are not scaled at all, while
    the center of the image is scaled in both x and y directions.
    """

    def __init__(self, image, xborder, yborder, tile=False):
        """
        @param image: The image (which may be a filename or image
        object) that will be scaled.

        @param xborder: The number of pixels in the x direction to use as
        a border.

        @param yborder: The number of pixels in the y direction to use as
        a border.

        @param tile: If true, instead of scaling a region, we tile that
        region.

        For better performance, have the image share a dimension
        length in common with the size the frame will be rendered
        at. We detect this and avoid scaling if possible.
        """

        super(Frame, self).__init__()

        self.image = Image(image)
        self.xborder = xborder
        self.yborder = yborder
        self.tile = tile

    def render(self, width, height, st, at):

        fi = renpy.display.im.FrameImage(self.image,
                                         self.xborder,
                                         self.yborder,
                                         width,
                                         height,
                                         self.tile)

        return render(fi, width, height, st, at)

    def visit(self):
        return [ self.image ]
                
class ImageButton(renpy.display.behavior.Button):
    """
    Used to implement the guts of an image button.
    """

    def __init__(self, idle_image, hover_image,
                 style='image_button',
                 image_style='image_button_image',
                 clicked=None, hovered=None, **properties):

        self.idle_image = renpy.easy.displayable(idle_image)
        self.idle_image.style.set_prefix("idle_")
        self.hover_image = renpy.easy.displayable(hover_image)
        self.hover_image.style.set_prefix("hover_")

        super(ImageButton, self).__init__(self.idle_image,
                                          style=style,
                                          clicked=clicked,
                                          hovered=hovered,
                                          **properties)
        
    def visit(self):
        return [ self.idle_image, self.hover_image ]

    def focus(self, default=False):
        self.child = self.hover_image
        super(ImageButton, self).focus(default=default)

    def unfocus(self):
        self.child = self.idle_image
        super(ImageButton, self).unfocus()

