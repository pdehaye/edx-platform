"""
Tests for wiki permissions
"""

from django.contrib.auth.models import Group
from student.tests.factories import UserFactory
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from django.test.utils import override_settings
from courseware.tests.factories import InstructorFactory, StaffFactory
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE

from wiki.models import URLPath
from course_wiki.views import get_or_create_root
from course_wiki.utils import user_is_article_course_staff, course_wiki_slug
from course_wiki import settings


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestWikiAccessBase(ModuleStoreTestCase):
    """Base class for testing wiki access."""
    def setUp(self):

        self.wiki = get_or_create_root()

        self.course_math101 = CourseFactory.create(org='org', number='math101', display_name='Course', metadata={'use_unique_wiki_id':'false'})
        self.course_math101_staff = self.create_staff_for_course(self.course_math101)

        wiki_math101 = self.create_urlpath(self.wiki, course_wiki_slug(self.course_math101))
        wiki_math101_page = self.create_urlpath(wiki_math101, 'Child')
        wiki_math101_page_page = self.create_urlpath(wiki_math101_page, 'Grandchild')
        self.wiki_math101_pages = [wiki_math101, wiki_math101_page, wiki_math101_page_page]

        self.course_math101b = CourseFactory.create(org='org', number='math101b', display_name='Course', metadata={'use_unique_wiki_id':'true'})
        self.course_math101b_staff = self.create_staff_for_course(self.course_math101b)

        wiki_math101b = self.create_urlpath(self.wiki, course_wiki_slug(self.course_math101b))
        wiki_math101b_page = self.create_urlpath(wiki_math101b, 'Child')
        wiki_math101b_page_page = self.create_urlpath(wiki_math101b_page, 'Grandchild')
        self.wiki_math101b_pages = [wiki_math101b, wiki_math101b_page, wiki_math101b_page_page]

    def create_urlpath(self, parent, slug):
        """Creates an article at /parent/slug and returns its URLPath"""
        return URLPath.create_article(parent, slug, title=slug)

    def create_staff_for_course(self, course):
        """Creates and returns users with instructor and staff access to course."""

        course_locator = loc_mapper().translate_location(course.id, course.location)
        return [
            InstructorFactory(course=course.location),  # Creates instructor_org/number/run role name
            StaffFactory(course=course.location),  # Creates staff_org/number/run role name
            InstructorFactory(course=course_locator),  # Creates instructor_org.number.run role name
            StaffFactory(course=course_locator),  # Creates staff_org.number.run role name
        ]


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestWikiAccess(TestWikiAccessBase):
    """Test wiki access for course staff."""
    def setUp(self):
        super(TestWikiAccess, self).setUp()

        self.course_310b = CourseFactory.create(org='org', number='310b', display_name='Course')
        self.course_310b_staff = self.create_staff_for_course(self.course_310b)
        self.course_310b2 = CourseFactory.create(org='org', number='310b_', display_name='Course')
        self.course_310b2_staff = self.create_staff_for_course(self.course_310b2)

        self.wiki_310b = self.create_urlpath(self.wiki, course_wiki_slug(self.course_310b))
        self.wiki_310b2 = self.create_urlpath(self.wiki, course_wiki_slug(self.course_310b2))

    def test_no_one_is_root_wiki_staff(self):
        all_course_staff = self.course_math101_staff + self.course_310b_staff + self.course_310b2_staff
        for course_staff in all_course_staff:
            self.assertFalse(user_is_article_course_staff(course_staff, self.wiki.article))

    def test_course_staff_is_course_wiki_staff(self):
        self.assertEqual(self.course_math101.wiki_id, 'math101')
        for page in self.wiki_math101_pages:
            for course_staff in self.course_math101_staff:
                self.assertTrue(user_is_article_course_staff(course_staff, page.article))

        self.assertEqual(self.course_math101b.wiki_id, 'org.math101b.Course')
        for page in self.wiki_math101b_pages:
            for course_staff in self.course_math101b_staff:
                self.assertTrue(user_is_article_course_staff(course_staff, page.article))

    def test_settings(self):
        for page in self.wiki_math101_pages:
            for course_staff in self.course_math101_staff:
                self.assertTrue(settings.CAN_DELETE(page.article, course_staff))
                self.assertTrue(settings.CAN_MODERATE(page.article, course_staff))
                self.assertTrue(settings.CAN_CHANGE_PERMISSIONS(page.article, course_staff))
                self.assertTrue(settings.CAN_ASSIGN(page.article, course_staff))
                self.assertTrue(settings.CAN_ASSIGN_OWNER(page.article, course_staff))

        for page in self.wiki_math101b_pages:
            for course_staff in self.course_math101b_staff:
                self.assertTrue(settings.CAN_DELETE(page.article, course_staff))
                self.assertTrue(settings.CAN_MODERATE(page.article, course_staff))
                self.assertTrue(settings.CAN_CHANGE_PERMISSIONS(page.article, course_staff))
                self.assertTrue(settings.CAN_ASSIGN(page.article, course_staff))
                self.assertTrue(settings.CAN_ASSIGN_OWNER(page.article, course_staff))

    def test_other_course_staff_is_not_course_wiki_staff(self):
        for page in self.wiki_math101_pages:
            for course_staff in self.course_math101b_staff:
                self.assertFalse(user_is_article_course_staff(course_staff, page.article))

        for page in self.wiki_math101_pages:
            for course_staff in self.course_310b_staff:
                self.assertFalse(user_is_article_course_staff(course_staff, page.article))

        for course_staff in self.course_310b_staff:
            self.assertFalse(user_is_article_course_staff(course_staff, self.wiki_310b2.article))

        for course_staff in self.course_310b2_staff:
            self.assertFalse(user_is_article_course_staff(course_staff, self.wiki_310b.article))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestWikiAccessForStudent(TestWikiAccessBase):
    """Test access for students."""
    def setUp(self):
        super(TestWikiAccessForStudent, self).setUp()

        self.student = UserFactory.create()

    def test_student_is_not_root_wiki_staff(self):
        self.assertFalse(user_is_article_course_staff(self.student, self.wiki.article))

    def test_student_is_not_course_wiki_staff(self):
        for page in self.wiki_math101_pages:
            self.assertFalse(user_is_article_course_staff(self.student, page.article))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestWikiAccessForNumericalCourseNumber(TestWikiAccessBase):
    """Test staff has access if course number is numerical and wiki slug has an underscore appended."""
    def setUp(self):
        super(TestWikiAccessForNumericalCourseNumber, self).setUp()

        self.course_200 = CourseFactory.create(org='org', number='200', display_name='Course')
        self.course_200_staff = self.create_staff_for_course(self.course_200)

        wiki_200 = self.create_urlpath(self.wiki, course_wiki_slug(self.course_200))
        wiki_200_page = self.create_urlpath(wiki_200, 'Child')
        wiki_200_page_page = self.create_urlpath(wiki_200_page, 'Grandchild')
        self.wiki_200_pages = [wiki_200, wiki_200_page, wiki_200_page_page]

    def test_course_staff_is_course_wiki_staff_for_numerical_course_number(self):  # pylint: disable=C0103
        for page in self.wiki_200_pages:
            for course_staff in self.course_200_staff:
                self.assertTrue(user_is_article_course_staff(course_staff, page.article))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestWikiAccessForOldFormatCourseStaffGroups(TestWikiAccessBase):
    """Test staff has access if course group has old format."""
    def setUp(self):
        super(TestWikiAccessForOldFormatCourseStaffGroups, self).setUp()

        self.course_math101c = CourseFactory.create(org='org', number='math101c', display_name='Course')
        Group.objects.get_or_create(name='instructor_math101c')
        self.course_math101c_staff = self.create_staff_for_course(self.course_math101c)

        wiki_math101c = self.create_urlpath(self.wiki, course_wiki_slug(self.course_math101c))
        wiki_math101c_page = self.create_urlpath(wiki_math101c, 'Child')
        wiki_math101c_page_page = self.create_urlpath(wiki_math101c_page, 'Grandchild')
        self.wiki_math101c_pages = [wiki_math101c, wiki_math101c_page, wiki_math101c_page_page]

    def test_course_staff_is_course_wiki_staff(self):
        for page in self.wiki_math101c_pages:
            for course_staff in self.course_math101c_staff:
                self.assertTrue(user_is_article_course_staff(course_staff, page.article))
